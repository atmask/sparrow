from flask import request
from .config import DefaultConfig as Config
from .receivers.events import *
from sparrow.logger import logger
import traceback

from sparrow.cloudproviders.exceptions import AuthenticationError
from sparrow.middleware.auth import BasicAuthMiddleware
from sparrow.sparrowfile.models import SparrowFile
from sparrow.sparrowfile.exceptions import ClusterNotDefinedError

from flask import Flask
from .config import *


app = Flask(__name__)
app.wsgi_app = BasicAuthMiddleware(app.wsgi_app)

@app.route(f'{Config.server_path_prefix}/webhook', methods=['POST'])
def on_event():
    # logger.info(f"Got payload: {request.json}")
    try:
        event = Config.receiver.getEvent(request.json)
        handle_event(event)
    except Exception as e:
        logger.warning(f"Exception: {e}")
        traceback.print_exc()
        Config.vcs.SetEventFailure(event)
    return "", 200

def handle_event(event: PullRequestEvent):
    logger.info(f"Handling Event: {event}")
    ## Ignore None events
    if event:
        match event.type:
            case (PullRequestEventType.COMMENT_DIFF | PullRequestEventType.MR_MODIFIED | PullRequestEventType.MR_OPENED):
                ## Update the VCS provider UI to acknowledge that changes are being processed
                Config.vcs.acknowledgeEvent(event)
                
                ## Get the changed files (old and new paths)
                logger.info("Getting changes")
                diffs = Config.vcs.getChanges(event)

                ## Clone the the repo
                logger.info("Cloning repo")
                repo_path = Config.vcs.cloneRepoAtSha(event)

                ## check if the changed files are dependencies of a chart
                changed_charts = Config.release_manager.detectChangedReleases(repo_path, diffs)

                ## Changed charts paths will be in the format:
                ## f'{settings.SPARROW_CLONE_DIR}/{repo-id}-{sha}/{path to chart in repo}'
                logger.debug(f"Changed charts paths: {changed_charts}")

                ## Load the repo sparrowfile
                try:
                    sparrowfile = SparrowFile.from_yaml(f"{repo_path}/sparrowfile.yaml")
                except FileNotFoundError:
                    logger.error(f"No sparrowfile found in the repo: {repo_path}")
                    Config.vcs.postComment(event, "No `sparrowfile.yaml` was found at the repo base. Cannot generate diff for these changes.")
                    return
                except ClusterNotDefinedError as e:
                    logger.error(f"Cluster not defined in sparrowfile: {e}")
                    Config.vcs.postComment(event, f"Cluster `{e.cluster_name}` is not defined in the sparrowfile. Cannot generate diff for these changes.")
                    return
                
                ## TODO: run a plan on the chart but lock the plan using a repo+path hash dir so that two mrs don't conflict
                diffs = []
                for chart in changed_charts:
                    ## Get the cluster values mapping for this chart from the sparrowfile
                    chart_configuration = sparrowfile.getChartConfiguration(chart)
                    chart_name = chart.removeprefix(f"{repo_path}/")

                    ## Mkae sure the chart has a configuration in the sparrowfile
                    if not chart_configuration:
                        Config.vcs.postComment(event, f"Configuration applicable to `{chart_name}` were not found in the sparrowfile. Cannot generate diff for this chart.")
                        continue

                    for env in chart_configuration.environments:
                        try:
                            with env.cluster.provider_config.authenticate():
                                ## Get the diff
                                logger.debug(f"Generating diff for chart {chart} in namespace {env.namespace} working with values files {env.valuesFiles}")
                                diffs.append({ 
                                    "chart": chart_name,
                                    "env": env.name,
                                    "diff": Config.release_manager.generateDiff(chart, chart_configuration.release_name, env.namespace, env.valuesFiles)
                                    })
                        except AuthenticationError as e:
                            logger.error(f"Could not authenticate with cluster: {e}")
                            Config.vcs.postComment(event, f"Could not authenticate with cluster: {e}")
                            return
                if diffs:

                    prologue = f"Ran diff for {len(diffs)} charts:\n"
                    diff_block = ""
                    epilogue = "* ⏩ To **apply all diffs** from this pull request, comment:\n  * `sparrow apply`\n"
                    epilogue += "* ⏩ To **apply specific diffs** from this pull request, comment:\n  * `sparrow apply -f <chart>@<environment>`\n\n"
                    
                    for index, diff in enumerate(diffs):
                        chart_name = diff.get('chart').removeprefix(f"{repo_path}/")
                        prologue += f"{index+1}. `{chart_name}` environment: `{diff.get('env')}`\n"
                    
                        diff_block += f"## {index+1}. `{diff.get('chart')}` environment: `{diff.get('env')}`\n"
                        diff_block += f"<details><summary>Show Diffs</summary>\n\n"
                        diff_block += f"```\n{diff.get('diff')}\n```\n\n"
                        diff_block += "</details>\n\n"
                    Config.vcs.postComment(event, f"{prologue}\n\n{diff_block}\n\n---\n{epilogue}")

            case PullRequestEventType.COMMENT_APPLY:
                ## Update the VCS provider UI to acknowledge that changes are being processed
                Config.vcs.acknowledgeEvent(event)

                ## Get the changed files (old and new paths)
                logger.info("Getting the MR changes")
                diffs = Config.vcs.getChanges(event)

                ## Clone the the repo
                logger.info("Cloning repo")
                repo_path = Config.vcs.cloneRepoAtSha(event)

                ## check if the changed files are dependencies of a chart
                changed_charts = Config.release_manager.detectChangedReleases(repo_path, diffs)

                ## Changed charts paths will be in the format:
                ## f'{settings.SPARROW_CLONE_DIR}/{repo-id}-{sha}/{path to chart in repo}'
                logger.debug(f"Changed charts paths: {changed_charts}")

                ## Load the repo sparrowfile
                try:
                    sparrowfile = SparrowFile.from_yaml(f"{repo_path}/sparrowfile.yaml")
                except FileNotFoundError:
                    logger.error(f"No sparrowfile found in the repo: {repo_path}")
                    Config.vcs.postComment(event, "No `sparrowfile.yaml` was found at the repo base. Cannot generate diff for these changes.")
                    return
                except ClusterNotDefinedError as e:
                    logger.error(f"Cluster not defined in sparrowfile: {e}")
                    Config.vcs.postComment(event, f"Cluster `{e.cluster_name}` is not defined in the sparrowfile. Cannot generate diff for these changes.")
                    return
                
                ## Filter the changed charts to only the ones that have been specified in the command
                user_targeted_charts = event.command.flags if event.command.flags else changed_charts
                logger.info(f"User targeted charts: {user_targeted_charts}")
                logger.info(f"Changed charts: {changed_charts}")
                valid_targeted_charts = []
                for user_targeted_chart in user_targeted_charts:
                    chart = user_targeted_chart.split('@')[0]
                    logger.debug(f"Checking if {chart} is in the changed charts")
                    if any(chart in changed_chart for changed_chart in changed_charts):
                        valid_targeted_charts.append(f"{repo_path}/{user_targeted_chart}")

                logger.debug(f"Valid targeted charts: {valid_targeted_charts}")
                for chart in valid_targeted_charts:
                    chart_path = chart.split('@')[0]
                    chart_env = chart.split('@')[1] if len(chart.split('@')) > 1 else None

                    ## Get the cluster values mapping for this chart from the sparrowfile
                    chart_configuration = sparrowfile.getChartConfiguration(chart_path)

                    ## Mkae sure the chart has a configuration in the sparrowfile
                    if not chart_configuration:
                        Config.vcs.postComment(event, f"Configuration applicable to `{chart_path}` were not found in the sparrowfile. Cannot generate diff for this chart.")
                        continue
                    
                    target_envs = []
                    if chart_env:
                        chart_env_config = chart_configuration.get_environment(chart_env)
                        if chart_env_config:
                            target_envs = [chart_env_config]
                        else:
                            Config.vcs.postComment(event, f"Environment `{chart_env}` not found in the chart configuration. Cannot apply changes...")
                            raise ValueError(f"Environment {chart_env} not found in the chart configuration")
                    else:
                        target_envs = chart_configuration.environments

                    
                    apply_logs = []
                    for env in target_envs:
                        try:
                            with env.cluster.provider_config.authenticate():
                                ## Apply the charts
                                logger.debug(f"Applying {chart} in namespace {env.namespace} working with values files {env.valuesFiles}")
                                apply_logs.append({ 
                                    "chart": chart_path,
                                    "env": env.name,
                                    "logs": Config.release_manager.performUpgradeOrInstall(chart_path, chart_configuration.release_name, env.namespace, env.valuesFiles)
                                    })
                        except AuthenticationError as e:
                            logger.error(f"Could not authenticate with cluster: {e}")
                            Config.vcs.postComment(event, f"Could not authenticate with cluster: {e}")
                            return
                        
                if apply_logs:

                    prologue = f"Ran apply for {len(apply_logs)} charts:\n"
                    log_block = ""
                    
                    for index, log in enumerate(apply_logs):
                        chart_name = log.get('chart').removeprefix(f"{repo_path}/")
                        prologue += f"{index+1}. `{chart_name}` environment: `{log.get('env')}`\n"
                    
                        log_block += f"## {index+1}. `{chart_name}` environment: `{log.get('env')}`\n"
                        log_block += f"<details><summary>Show Apply Logs</summary>\n\n"
                        log_block += f"```\n{log.get('logs')}\n```\n\n"
                        log_block += "</details>\n\n"
                    Config.vcs.postComment(event, f"{prologue}\n\n{log_block}\n")

            case PullRequestEventType.COMMENT_SUGGESTION:
                '''
                Send a suggested command back to the user
                '''
                Config.vcs.acknowledgeEvent(event)
                return

            case _:
                raise ValueError(f"Invalid event type cannot be handled: {event.type}")
        
        ## Set the pipeline status to success
        Config.vcs.SetEventSuccess(event)


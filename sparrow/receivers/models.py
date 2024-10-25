from sparrow.logger import logger
from thefuzz import fuzz
from .events import PullRequestEventType, Command 

from sparrow.parser.argsparse import SparrowCommandParser
from sparrow.parser.exceptions import ArgumentError


class Comment:
    SUGGESTION_STR = "`{received_command}` is not a recognized command. Did you mean `{suggestion}`?"
    VALID_COMMANDS = ["sparrow apply", "sparrow diff"]
    COMMAND_MISTAKES = {
        "sparrow upgrade": "sparrow apply",
        "sparrow plan": "sparrow diff",
        "helm diff": "sparrow diff",
        "helm upgrade": "sparrow apply"
    }

    def __init__(self, comment: str):
        self.comment = comment.lower().strip()
        self._parser = self._create_parser()

    def _create_parser(self) -> SparrowCommandParser:
        parser = SparrowCommandParser()
        parser.add_argument('command', help='Command to execute', choices=['sparrow'])
        parser.add_argument('subcommand', help='Subcommand to execute', choices=['apply', 'diff'])
        parser.add_argument('-f', '--file', action='append', help='File path', required=False)
        return parser
            
    def parseCommand(self) -> Command:
        try:
            if not self.comment.startswith('sparrow'):
                raise ArgumentError("Command must start with `sparrow`") ## Otherwise diffs will get processed and this gets messy
            args = self._parser.parse_from_str(self.comment)
        except ArgumentError:
            if suggest := self.getSuggestion():
                return Command(PullRequestEventType.COMMENT_SUGGESTION, suggest, None)
            else:
                return Command(None, None, None)
        else:
            if args.subcommand == 'apply':
                return Command(PullRequestEventType.COMMENT_APPLY, None, args.file)
            elif args.subcommand == 'diff':
                return Command(PullRequestEventType.COMMENT_DIFF, None, args.file)
    
    def getSuggestion(self, threshold=70):
        '''
        compute distance and offer a suggestion or none
        '''
        match_dict = {}
        ## Find the closest match
        for suggestion in Comment.VALID_COMMANDS + list(Comment.COMMAND_MISTAKES.keys()):
            match_dict[suggestion] = fuzz.ratio(self.comment, suggestion)

        logger.info(f"Suggestion Dict: {match_dict}")
        closest = max(match_dict, key=match_dict.get)
        logger.debug(f"Closest suggestion for {self.comment} is {closest} with ratio: {match_dict.get(closest)}")

        ## Validate that the suggestion meets the threshold req
        if match_dict[closest] < threshold:
            return None

        ## Do any mapping from mistakes to correct commands
        closest = Comment.COMMAND_MISTAKES.get(closest) if Comment.COMMAND_MISTAKES.get(closest) else closest
        logger.debug(f"After mappings the suggestion is: {closest}")

        suggest = Comment.SUGGESTION_STR.format(received_command=self.comment, suggestion=closest)
        return suggest 
        
        

from marshmallow import Schema, fields, post_load, EXCLUDE
from sparrow.vcs.gitlab import enum
from sparrow.vcs.gitlab import models as gitlab_models
from sparrow.vcs import models


class NoteBodySchema(Schema):
    '''Schema for notes payload that posts/gets a comment'''
    body = fields.Str()

class EmojiBodySchema(Schema):
    '''Schema body for awarding an emoji reaction'''
    name = fields.Str()

class CommitStatusBodySchema(Schema):
    '''
    Schema of payload to Commit Status update
    '''
    # SKIP_VALUES = set([None])

    # @post_dump
    # def remove_skip_values(self, data):
    #     '''Drop values that are note set'''
    #     return {
    #         key: value for key, value in data.items()
    #         if value not in self.SKIP_VALUES
    #     }
    # project_id = fields.Int(data_key="id")
    # commit_sha = fields.Str(data_key="sha")
    # pipeline_id = fields.Int()
    commit_state = fields.Enum(enum=enum.CommitState, data_key="state", by_value=True)
    name = fields.Enum(enum=enum.CommitStatusName, by_value=True)
    description = fields.Enum(enum=enum.CommitStatusDescription, by_value=True)

class PipelineSchema(Schema):
    id = fields.Int()

    @post_load
    def make_object(self, data, **kwargs) -> gitlab_models.GitlabPipeline:
        return gitlab_models.GitlabPipeline(**data)

class MergeRequestDiff(Schema):
    old_path = fields.Str()
    new_path = fields.Str()

    class Meta:
        unknown = EXCLUDE

    @post_load
    def make_object(self, data, **kwargs) -> models.MergeRequestDiff:
        return models.MergeRequestDiff(**data)


from marshmallow import Schema, fields, EXCLUDE, post_load
from sparrow.receivers.gitlab import enum
from sparrow.receivers.gitlab import models

class GitlabUserSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Int()
    name = fields.Str()
    username = fields.Str()
    email = fields.Str()

    @post_load
    def make_object(self, data, **kwargs):
        return models.GitlabUser(**data)

class GitlabProjectSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Int()
    name = fields.Str()
    web_url = fields.Str()
    namespace = fields.Str()
    git_http_url = fields.Str()

    @post_load
    def make_object(self, data, **kwargs):
        return models.GitlabProject(**data)

class GitlabRepositorySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    name = fields.Str()
    url = fields.Str()
    homepage = fields.Str()

    @post_load
    def make_object(self, data, **kwargs):
        return models.GitlabRepository(**data)

class GitlabLastCommitSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    sha = fields.Str(data_key="id")

    @post_load
    def make_object(self, data, **kwargs):
        return models.GitlabLastCommit(**data)

class GitlabMergeRequestSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Int()
    iid = fields.Int()
    target_branch = fields.Str()
    source_branch = fields.Str()
    last_commit = fields.Nested(GitlabLastCommitSchema)
    action = fields.Enum(enum=enum.GitlabMergeRequestAction, by_value=True, load_default=None) # Not passed when manually triggering events
    
    @post_load
    def make_object(self, data, **kwargs):
        return models.GitlabMergeRequest(**data)

class GitlabCommentSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Int()
    comment = fields.Str(data_key="note")
    noteable_type = fields.Enum(enum=enum.GitlabCommentType, by_value=True)

    @post_load
    def make_object(self, data, **kwargs):
        return models.GitlabComment(**data)

class GitlabWebhookEventSchema(Schema):
    '''
    Provides a generics schema of shared fields between gitlab events
    '''
    class Meta:
        unknown = EXCLUDE

    event_type = fields.Enum(enum=enum.GitlabWebookEventType, by_value=True)
    user = fields.Nested(GitlabUserSchema)
    project = fields.Nested(GitlabProjectSchema)
    repository = fields.Nested(GitlabRepositorySchema)

    @post_load
    def make_object(self, data, **kwargs):
        return models.GitlabWebhookEvent(**data)

class MergeRequestEventSchema(GitlabWebhookEventSchema):
    '''
     Provides a schema of incoming webhook even and deserializes to object
    '''
    object_attributes = fields.Nested(GitlabMergeRequestSchema)

    @post_load
    def make_object(self, data, **kwargs):
        return models.MergeRequestEvent(**data)

class CommentEventSchema(GitlabWebhookEventSchema):
    '''
     Provides a schema for general comment/note events. Can be a comment on many types not just merge request
    '''
    object_attributes = fields.Nested(GitlabCommentSchema)

    @post_load
    def make_object(self, data, **kwargs):
        return models.CommentEvent(**data)

class MergeRequestCommentEventSchema(CommentEventSchema):
    '''
    A Merge Request Comment type
    '''
    merge_request = fields.Nested(GitlabMergeRequestSchema)
    
    @post_load
    def make_object(self, data, **kwargs):
        return models.MergeRequestCommentEvent(**data)


        

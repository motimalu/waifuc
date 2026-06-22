import os
from waifuc.source import VideoSource
from waifuc.action import TaggingAction
from waifuc.action.tagging import BlacklistedTagDropAction, TagNSFWOrExplicitAction, TagOverlapDropAction
from waifuc.export import TextualInversionExporter

if __name__ == '__main__':
    source = VideoSource.from_directory('../../data/videos')
    source.attach(
        TaggingAction(force=True),
        TagOverlapDropAction(),
        BlacklistedTagDropAction(),
        TagNSFWOrExplicitAction(),
    ).export(
        TextualInversionExporter('../../data/images')
    )

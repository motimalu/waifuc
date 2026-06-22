from waifuc.source import LocalTISource
from waifuc.action import TaggingAction
from waifuc.action.tagging import BlacklistedTagDropAction
from waifuc.export import TextualInversionExporter

if __name__ == '__main__':
    filenames = ['']
    for file in filenames:
        source = LocalTISource('../../data/' + file) 
        source.attach(
            TaggingAction(force=True),
            BlacklistedTagDropAction(),
        ).export(
            TextualInversionExporter('../../data/' + file, use_escape=False)
        )

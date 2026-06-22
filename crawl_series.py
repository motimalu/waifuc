import os
from waifuc.action import NoMonochromeAction, FilterSimilarAction, \
    TaggingAction, FirstNSelectAction, ModeConvertAction
from waifuc.action.filter import BlacklistedTagFilterAction, ExistingDanbooruFileFilterAction, FileTypeFilterAction, MinAreaFilterAction
from waifuc.action.safety import SafetyAction
from waifuc.action.tagging import BlacklistedTagDropAction, DanbooruTagProcessAction, TagOverlapDropAction, TagRemoveUnderlineAction
from waifuc.export import TextualInversionExporter
from waifuc.source import DanbooruSource

USER_NAME = os.getenv("USER_NAME")
USER_VAR = os.getenv("USER_VAR")

if __name__ == '__main__':
    name = ''
    s = DanbooruSource([name, '-comic'], 800, True, USER_NAME, USER_VAR)
    output_dir = '/data/1_collection_name3/0_updat/1_' + name
    count = 400
    s.attach(

        # Filter GIF
        FileTypeFilterAction(),
        
        # Filter existing files
        ExistingDanbooruFileFilterAction(),

        # Filter blacklisted tags
        BlacklistedTagFilterAction(),

        # preprocess images with a white background RGB
        ModeConvertAction('RGB', 'white'),

        # pre-filtering for images
        NoMonochromeAction(),  # no monochrome, greyscale or sketch
        # ClassFilterAction(['illustration', 'bangumi']),  # no comic

        MinAreaFilterAction(512),

        FilterSimilarAction('all'),  # filter duplicated images

        SafetyAction(),

        # TaggingAction(force=True),

        BlacklistedTagDropAction(),

        DanbooruTagProcessAction([
        'ai-generated',
        'ai-assisted',
        'adversarial_noise',
        'absurdres',
        'lowres',
        'traditional_media',
        'official_art',
        'concept_art',
        'acrylic_paint_(medium)',
        'airbrush_(medium)',
        'ballpoint_pen_(medium)',
        'brush_(medium)',
        'chalk_(medium)',
        'calligraphy_brush_(medium)',
        'canvas_(medium)',
        'charcoal_(medium)',
        'colored_pencil_(medium)',
        'color_ink_(medium)',
        'coupy_pencil_(medium)',
        'crayon_(medium)',
        'gouache_(medium)',
        'graphite_(medium)',
        'ink_(medium)',
        'marker_(medium)',
        'millipen_(medium)',
        'nib_pen_(medium)',
        'oil_painting_(medium)',
        'painting_(medium)',
        'pastel_(medium)',
        'photo_(medium)',
        'tempera_(medium)',
        'watercolor_(medium)',
        'watercolor_pencil_(medium)'
        ], output_dir),

        TagOverlapDropAction(),

        TagRemoveUnderlineAction(),

        FirstNSelectAction(count),
    ).export(
        TextualInversionExporter(output_dir, False, True)
    )
    

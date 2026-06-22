from functools import partial
import os
from typing import Iterator, Union, List, Mapping, Literal

from PIL import Image
from imgutils.tagging import get_deepdanbooru_tags, get_wd14_tags, get_mldanbooru_tags, drop_overlap_tags, \
    is_blacklisted, remove_underline
from imgutils.validate import anime_rating
from imgutils.metrics import anime_dbaesthetic
from .base import ProcessAction, BaseAction
from ..model import ImageItem
import json
from pathlib import Path


def _deepdanbooru_tagging(image: Image.Image, use_real_name: bool = False,
                          general_threshold: float = 0.5, character_threshold: float = 0.5, **kwargs):
    _ = kwargs
    _, features, characters = get_deepdanbooru_tags(image, use_real_name, general_threshold, character_threshold)
    return {**features, **characters}


def _wd14_tagging(image: Image.Image, model_name: str,
                  general_threshold: float = 0.35, character_threshold: float = 0.85, **kwargs):
    _ = kwargs
    _, features, characters = get_wd14_tags(
        image,
        model_name=model_name,
        general_threshold=general_threshold,
        character_threshold=character_threshold,
    )
    return {**features, **characters}


def _mldanbooru_tagging(image: Image.Image, use_real_name: bool = False, general_threshold: float = 0.7, **kwargs):
    _ = kwargs
    features = get_mldanbooru_tags(image, use_real_name, general_threshold)
    return features


_TAGGING_METHODS = {
    'deepdanbooru': _deepdanbooru_tagging,
    'wd14_vit': partial(_wd14_tagging, model_name='ViT'),
    'wd14_convnext': partial(_wd14_tagging, model_name='ConvNext'),
    'wd14_convnextv2': partial(_wd14_tagging, model_name='ConvNextV2'),
    'wd14_swinv2': partial(_wd14_tagging, model_name='SwinV2'),
    'wd14_moat': partial(_wd14_tagging, model_name='MOAT'),
    'wd14_v3_swinv2': partial(_wd14_tagging, model_name='SwinV2_v3'),
    'wd14_v3_convnext': partial(_wd14_tagging, model_name='ConvNext_v3'),
    'wd14_v3_vit': partial(_wd14_tagging, model_name='ViT_v3'),
    'wd14_v3_eva02_large': partial(_wd14_tagging, model_name='EVA02_Large'),
    'wd14_v3_vit_large': partial(_wd14_tagging, model_name='ViT_Large'),
    'mldanbooru': _mldanbooru_tagging,
}

TaggingMethodTyping = Literal[
    'deepdanbooru', 'wd14_vit', 'wd14_convnext', 'wd14_convnextv2', 'wd14_swinv2', 'mldanbooru',
    'wd14_moat', 'wd14_v3_swinv2', 'wd14_v3_convnext', 'wd14_v3_vit', 'wd14_v3_eva02_large', 'wd14_v3_vit_large'
]

DEFAULT_TAGGING_METHOD: TaggingMethodTyping = 'wd14_v3_eva02_large'

class TaggingAction(ProcessAction):
    def __init__(self, method: TaggingMethodTyping = DEFAULT_TAGGING_METHOD, force: bool = False, **kwargs):
        self.method = _TAGGING_METHODS[method]
        self.force = force
        self.kwargs = kwargs

    def process(self, item: ImageItem) -> ImageItem:
        if 'tags' in item.meta and not self.force:
            return item
        else:
            tags = self.method(image=item.image, **self.kwargs)
            return ImageItem(item.image, {**item.meta, 'tags': tags})


class TagFilterAction(BaseAction):
    # noinspection PyShadowingBuiltins
    def __init__(self, tags: Union[List[str], Mapping[str, float]],
                 method: TaggingMethodTyping = DEFAULT_TAGGING_METHOD, reversed: bool = False, **kwargs):
        if isinstance(tags, (list, tuple)):
            self.tags = {tag: 1e-6 for tag in tags}
        elif isinstance(tags, dict):
            self.tags = dict(tags)
        else:
            raise TypeError(f'Unknown type of tags - {tags!r}.')
        self.tagger = TaggingAction(method, force=False, **kwargs)
        self.reversed = reversed

    def iter(self, item: ImageItem) -> Iterator[ImageItem]:
        item = self.tagger(item)
        tags = item.meta['tags']

        valid = True
        for tag, min_score in self.tags.items():
            tag_score = tags.get(tag, 0.0)
            if (not self.reversed and tag_score < min_score) or \
                    (self.reversed and tag_score > min_score):
                valid = False
                break

        if valid:
            yield item

    def reset(self):
        self.tagger.reset()


class TagOverlapDropAction(ProcessAction):
    def process(self, item: ImageItem) -> ImageItem:
        tags = drop_overlap_tags(dict(item.meta.get('tags') or {}))
        return ImageItem(item.image, {**item.meta, 'tags': tags})

class DanbooruMetaProcessAction(ProcessAction):
    def __init__(self, meta_whitelist: List[str], output_dir: str):
        self.meta_whitelist = set(meta_whitelist)
        self.output_dir = Path(output_dir)

    def process(self, item: ImageItem) -> ImageItem:
        danbooru = item.meta.get('danbooru') or {}

        # Save Danbooru meta to _meta json
        output_dir = '/data/0_danbooru_meta'
        filename = item.meta['filename']
        full_filename = os.path.join(output_dir, filename)
        full_directory = os.path.dirname(full_filename)
        full_metaname = os.path.join(output_dir, os.path.splitext(filename)[0] + '_meta.json')

        if full_directory:
            os.makedirs(full_directory, exist_ok=True)
        with open(full_metaname, 'w', encoding='utf-8') as f:
            json.dump(danbooru, f, indent=4)

        return ImageItem({}, {**item.meta })

class DanbooruTagProcessAction(ProcessAction):
    def __init__(self, meta_whitelist: List[str], output_dir: str):
        self.meta_whitelist = set(meta_whitelist)
        self.output_dir = Path(output_dir)

    def process(self, item: ImageItem) -> ImageItem:
        tags = dict(item.meta.get('tags') or {})
        danbooru = item.meta.get('danbooru') or {}

        # Save Danbooru meta to _meta json
        filename = item.meta['filename']
        full_filename = os.path.join(self.output_dir, filename)
        full_directory = os.path.dirname(full_filename)
        full_metaname = os.path.join(self.output_dir, os.path.splitext(filename)[0] + '_meta.json')

        if full_directory:
            os.makedirs(full_directory, exist_ok=True)
        with open(full_metaname, 'w', encoding='utf-8') as f:
            json.dump(danbooru, f, indent=4)

        if danbooru:
            meta = danbooru.get('tag_string_meta', None) or ''
            characters = danbooru.get('tag_string_character', None) or ''
            copyrights = danbooru.get('tag_string_copyright', None) or ''
            artists = danbooru.get('tag_string_artist', None) or ''
            rating = danbooru.get('rating')
            if rating == "e":
                tags["explicit"] = 0
            if rating == "q":
                tags["nsfw"] = 0
            # Drop meta tags, sort desc whitelisted
            for meta_tag in meta.split():
                if meta_tag in self.meta_whitelist:
                    tags[meta_tag] = 0
                elif tags.get(meta_tag):
                    del tags[meta_tag]
            # Sort asc characters copyrights and artists
            for character in characters.split():
                tags[character] = 2.9
            for copyright in copyrights.split():
                tags[copyright] = 2.8
            # pre-pend '@:' for artist tags
            for artist in artists.split():
                tags[artist] = 2.7
                by_artist = '@' + artist
                tags[by_artist] = tags[artist]
                del tags[artist]
        return ImageItem(item.image, {**item.meta, 'tags': tags})

class TagNSFWOrExplicitAction(ProcessAction):
    def process(self, item: ImageItem) -> ImageItem:
        [rating, score] = anime_rating(item.image)
        tags = dict(item.meta.get('tags') or {})
        # Tag r15 as "nsfw"
        if rating == 'r15':
            tags["nsfw"] = score
        # Tag r18 as "explicit"
        if rating == 'r18':
            tags["explicit"] = score
        return ImageItem(item.image, {**item.meta, 'tags': tags})

QUALITY_TAGS = ["absurdres", "masterpiece", "best quality", "very aesthetic", "aesthetic", "low quality", "worst quality"]

class SortQualityRatingsAction(ProcessAction):
    def process(self, item: ImageItem) -> ImageItem:
        tags = dict(item.meta.get('tags') or {})
        for tag, score in tags.items():
            for i, quality in enumerate(reversed(QUALITY_TAGS)):
                if quality == tag:
                    tags[quality] = i * 0.0001
        return ImageItem(item.image, {**item.meta, 'tags': tags})

class TagDropAction(ProcessAction):
    def __init__(self, tags_to_drop: List[str]):
        self.tags_to_drop = set(tags_to_drop)

    def process(self, item: ImageItem) -> ImageItem:
        tags = dict(item.meta.get('tags') or {})
        tags = {tag: score for tag, score in tags.items() if tag not in self.tags_to_drop}
        return ImageItem(item.image, {**item.meta, 'tags': tags})


class BlacklistedTagDropAction(ProcessAction):
    def process(self, item: ImageItem) -> ImageItem:
        tags = dict(item.meta.get('tags') or {})
        tags = {tag: score for tag, score in tags.items() if not is_blacklisted(tag)}
        return ImageItem(item.image, {**item.meta, 'tags': tags})


class TagRemoveUnderlineAction(ProcessAction):
    def process(self, item: ImageItem) -> ImageItem:
        tags = dict(item.meta.get('tags') or {})
        tags = {remove_underline(tag): score for tag, score in tags.items()}
        return ImageItem(item.image, {**item.meta, 'tags': tags})

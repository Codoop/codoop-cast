from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'runtime/codoop-cast'))
from castlib import assets
from castlib.common import read_json, write_json
from castlib.contracts import index_artifacts, validate_partial


class AssetHandoffTests(unittest.TestCase):
    def test_collection_attaches_to_valid_scene_package_with_explicit_references(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = root/'working-scenes'
            shutil.copytree(ROOT/'examples/72-second-workflow', package)
            for kind in ('audio', 'alignment', 'timeline'):
                (package/(kind+'.json')).unlink()
            image = root/'diagram.svg'
            image.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>', encoding='utf-8')
            manifest = root/'draft.json'
            write_json(manifest, dict(items=[dict(id='topic-diagram', source_file=str(image), origin='Local agent diagram', usage_notes='Overview illustration', provenance=dict(source_type='code'))]))
            collection = assets.build(manifest, root/'assets-v001')
            assets.attach(collection['assets'], package)
            ref = collection['reference']
            storyboard = read_json(package/'video-script.json')
            storyboard['revision'] += 1
            storyboard['data']['assets'] = ref
            storyboard['data']['scenes'][0]['asset_ids'] = ['topic-diagram']
            write_json(package/'video-script.json', storyboard)
            scene = read_json(package/'scene.json')
            scene['revision'] += 1
            scene['data']['video-script'] = dict(artifact_id=storyboard['artifact_id'], revision=storyboard['revision'])
            for item in scene['data']['items']:
                item.update(status='ready', entry='scenes/index.html')
            scene['data']['items'][0]['asset_ids'] = ['topic-diagram']
            write_json(package/'scene.json', scene)
            index_artifacts(package)
            self.assertEqual(validate_partial(package, 'scenes')['status'], 'ready')
            image.unlink()
            self.assertEqual(assets.validate(package/'assets.json')['items'], 1)
            media = package/read_json(package/'assets.json')['data']['items'][0]['path']
            media.unlink()
            with self.assertRaises(ValueError):
                validate_partial(package, 'scenes')

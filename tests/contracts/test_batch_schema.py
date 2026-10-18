import sys,tempfile,unittest
from pathlib import Path
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'runtime/codoop-cast'))
from castlib import batch
from castlib.common import read_json

class BatchSchemaTests(unittest.TestCase):
 def test_saved_queue_transitions_match_public_schema(self):
  validator=Draft202012Validator(read_json(ROOT/'schemas/cast-batch.schema.json'))
  with tempfile.TemporaryDirectory() as tmp:
   directory=Path(tmp)/'batch';batch.create(directory);validator.validate(read_json(directory/'cast-batch.json'))
   result=batch.add(directory,topic='示例话题',target='research');ident=result['item_id']
   batch.next_item(directory);validator.validate(read_json(directory/'cast-batch.json'))
   batch.control(directory,'pause');batch.control(directory,'cancel');validator.validate(read_json(directory/'cast-batch.json'))
   batch.control(directory,'defer',ident,'test material unavailable',True)
   batch.control(directory,'resume');batch.control(directory,'retry',ident);batch.next_item(directory)
   validator.validate(read_json(directory/'cast-batch.json'))

if __name__=='__main__':unittest.main()

# coding: utf-8

import json, unittest, requests

prefix = 'http://api.iyengarlabs.org/v1/'
nodelete = False

class TestSubjectAndWork(unittest.TestCase):
    """Subject unit test stubs"""

    def testSubjectRemoveAllButRoot(self):
        # model = swagger_client.models.subject.Subject()  # noqa: E501
        removeAllButRoot(self, 'subject')
    # def testWorkRemoveAllButRoot(self):
        removeAllButRoot(self, 'work')
    # def testWorkRemoveAllButRoot(self):
        removeAllButRoot(self, 'person')

def removeAllButRoot(self, entity):
    response = requests.get(prefix + 'root' + entity)
    self.assertEqual(200, response.status_code)
    responseAsDict = json.loads(response.text)
    # print(responseAsDict)
    self.assertIn(entity, responseAsDict)
    field = {'subject':'title', 'work':'title', 'person':'name'}[entity]
    self.assertIn(field, responseAsDict[entity])
    if entity + '_relations' in responseAsDict[entity]:
        entity_relations = responseAsDict[entity][entity + '_relations']
        for entry in entity_relations:
            if nodelete: print('from root %s -  child will be deleted %s' % (entity, entry['id']))
            else:
                print('from root %s -  child is deleted %s' % (entity, entry['id']))
                response = requests.delete(prefix + entity + '/remove/' + entry['id'] + '?deletesubtree=true')
                self.assertIn(response.status_code, [200, 201])
                self.assertEqual('"OK"', response.text)
if __name__ == '__main__':
    unittest.main()

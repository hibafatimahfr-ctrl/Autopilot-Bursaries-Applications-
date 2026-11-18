import unittest
from app.core import score, merge, uid
class Tests(unittest.TestCase):
    def test_match(self):
        r=score({'kind':'candidate','title':'Women in engineering award','summary':'Canada','verified':False},{'program_keywords':['engineering'],'interests':['women in STEM']})
        self.assertGreater(r['score'],0)
        self.assertIn('verify',r['status'])
    def test_directory(self):
        self.assertEqual(score({'kind':'directory'},{} )['status'],'directory')
    def test_dedup(self):
        u=uid('https://example.org/a'); items,added=merge([{'id':u,'title':'A'}],[{'id':u,'title':'B'}]);self.assertEqual(len(items),1);self.assertFalse(added)
if __name__=='__main__':unittest.main()

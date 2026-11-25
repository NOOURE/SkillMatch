import tempfile
import unittest
from pathlib import Path
from database import initialize, get_offers, set_status
from matching import rank_offers, parse_skills, tokens

class SkillMatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / 'test.db'
        initialize(self.db)
    def tearDown(self):
        self.tmp.cleanup()
    def test_seed_and_filters(self):
        initialize(self.db)
        self.assertEqual(len(get_offers(self.db)), 12)
        results = get_offers(self.db, 'Nantes', 'Stage')
        self.assertTrue(results)
        self.assertTrue(all(o['city']=='Nantes' and o['contract']=='Stage' for o in results))
    def test_exact_skill_ranking(self):
        results = rank_offers(get_offers(self.db), 'C++, Algorithmique, Git, Linux, Tests')
        self.assertEqual(results[0]['title'], 'Développeur C++')
        self.assertEqual(results[0]['coverage'],100)
        self.assertFalse(results[0]['missing'])
        self.assertTrue(all(0 <= o['score'] <= 100 for o in results))
    def test_empty_profile(self):
        self.assertTrue(all(o['score']==0 for o in rank_offers(get_offers(self.db), '')))
    def test_normalization(self):
        self.assertEqual(parse_skills('SQL, POO; Réseaux, sql'), {'sql','poo','reseaux'})
        self.assertEqual(tokens('C++ C# TF-IDF'), ['c++','c#','tf-idf'])
    def test_status_persistence(self):
        set_status(1,'Entretien',self.db)
        self.assertEqual(get_offers(self.db)[0]['status'],'Entretien')
        with self.assertRaises(ValueError):
            set_status(1,'invalid',self.db)
    def test_unmatched(self):
        results = rank_offers(get_offers(self.db), 'compétenceinexistante')
        self.assertTrue(all(o['coverage']==0 and o['score']==0 for o in results))

if __name__=='__main__':
    unittest.main()

import unittest
from datetime import datetime, timezone, timedelta
import mongomock
import hashlib
from repair_migration import plan, apply, WIRTZ_KEEP, WIRTZ_DUPLICATE, WIRTZ_CLUB


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.db = mongomock.MongoClient().transfernews_db
        self.now = datetime(2026, 9, 20, tzinfo=timezone.utc)

    def test_duplicate_urls_and_unknown_players_are_reversible(self):
        for n in range(3):
            self.db.articles.insert_one({"_id": str(n), "id": str(n), "slug": "same", "status": "published", "player_name": "Known Player", "published_at": self.now - timedelta(days=30-n), "body": "unchanged"})
        self.db.articles.insert_one({"_id": "unknown", "id": "unknown", "slug": "unknown", "player_name": "Unbekannter Spieler", "status": "published"})
        operations = plan(self.db, self.now)
        apply(self.db, operations)
        self.assertEqual(self.db.articles.count_documents({"status": "published"}), 1)
        self.assertEqual(self.db.articles.find_one({"slug": "same"})["id"], "0")
        self.assertEqual(len(set(a["slug"] for a in self.db.articles.find())), 4)
        self.assertEqual(self.db.repair_archive.count_documents({"collection": "articles"}), 4)
        self.assertEqual(self.db.articles.find_one({"id": "0"})["body"], "unchanged")
        self.assertEqual(plan(self.db, self.now)["articles"], {})

    def test_only_old_unprocessed_queue_is_removed_and_archived(self):
        for key, status, age in [("old", "pending", 4), ("fresh", "pending", 1), ("done", "processed", 5)]:
            self.db.events.insert_one({"_id": key, "status": status, "created_at": self.now-timedelta(days=age)})
        operations = plan(self.db, self.now)
        self.assertEqual(operations["old_events"], ["old"])
        self.assertEqual(apply(self.db, operations), 1)
        self.assertEqual(self.db.events.count_documents({}), 2)
        self.assertEqual(self.db.repair_archive.count_documents({"collection": "events"}), 1)

    def test_story_identity_duplicates_keep_one_active_record(self):
        for n in range(2):
            self.db.transfer_stories.insert_one({"_id": str(n), "story_key": "same"})
        apply(self.db, plan(self.db, self.now))
        self.assertEqual(self.db.transfer_stories.count_documents({"story_key": "same"}), 1)
        self.assertEqual(self.db.transfer_stories.count_documents({}), 2)

    def test_real_author_is_preserved_and_completed_run_ignores_new_content(self):
        self.db.authors.insert_one({"id":"real", "slug":"real-author", "name":"Real Author"})
        self.db.articles.insert_one({"_id":"old", "id":"old", "slug":"old", "author_id":"real", "author_slug":"real-author", "author_name":"Real Author"})
        apply(self.db, plan(self.db, self.now))
        self.assertEqual(self.db.articles.find_one({"_id":"old"})["author_name"], "Real Author")
        self.db.articles.insert_one({"_id":"new", "id":"new", "slug":"new", "author_name":"New human author"})
        self.db.events.insert_one({"_id":"later-backlog", "status":"pending", "created_at":self.now-timedelta(days=5)})
        rerun=plan(self.db,self.now+timedelta(days=30))
        self.assertTrue(rerun["already_completed"])
        self.assertEqual(apply(self.db,rerun),0)
        self.assertEqual(self.db.articles.find_one({"_id":"new"})["author_name"],"New human author")
        self.assertIsNotNone(self.db.events.find_one({"_id":"later-backlog"}))

    def test_generated_slug_collision_uses_longer_stable_suffix(self):
        suffix=hashlib.sha256(b"duplicate").hexdigest()[:12]
        for identity,slug in [("keep","same"),("duplicate","same"),("existing","same-"+suffix)]:
            self.db.articles.insert_one({"_id":identity,"id":identity,"slug":slug,"status":"published","published_at":self.now+(timedelta(seconds=1) if identity=="duplicate" else timedelta())})
        first=plan(self.db,self.now); second=plan(self.db,self.now)
        self.assertEqual(first["articles"]["duplicate"]["slug"],second["articles"]["duplicate"]["slug"])
        self.assertNotEqual(first["articles"]["duplicate"]["slug"],"same-"+suffix)
        apply(self.db,first)
        self.assertEqual(self.db.articles.count_documents({}),3)

    def test_blank_story_keys_and_archived_key_collisions_are_preflighted(self):
        suffix=hashlib.sha256(b"duplicate").hexdigest()[:12]
        for identity,key in [("keep","same"),("duplicate","same"),("existing","same:archived:"+suffix),("blank1",""),("blank2","")]:
            self.db.transfer_stories.insert_one({"_id":identity,"story_key":key,"created_at":self.now+(timedelta(seconds=1) if identity=="duplicate" else timedelta())})
        apply(self.db,plan(self.db,self.now))
        rows=list(self.db.transfer_stories.find())
        self.assertEqual(len({r['story_key'] for r in rows}),5)
        self.assertTrue(self.db.transfer_stories.find_one({'_id':'blank1'})['repair_archived'])

    def test_story_reference_follows_canonical_article_even_without_duplicate_story(self):
        self.db.articles.insert_many([
            {"_id":"a1","id":"a1","slug":"same","status":"published","published_at":self.now-timedelta(days=2)},
            {"_id":"a2","id":"a2","slug":"same","status":"published","published_at":self.now-timedelta(days=1)},
        ])
        self.db.transfer_stories.insert_one({"_id":"story","story_key":"story","article_id":"a2"})
        apply(self.db,plan(self.db,self.now))
        self.assertEqual(self.db.transfer_stories.find_one({"_id":"story"})['article_id'],'a1')
        self.assertEqual(self.db.articles.find_one({"_id":"a2"})['status'],'draft')

    def test_changed_source_is_rejected_before_any_archive_or_mutation(self):
        self.db.articles.insert_one({'_id':'one','slug':'one'})
        operations=plan(self.db,self.now)
        self.db.articles.update_one({'_id':'one'},{'$set':{'body':'new human edit'}})
        with self.assertRaises(RuntimeError): apply(self.db,operations)
        self.assertEqual(self.db.repair_archive.count_documents({}),0)
        self.assertNotIn('author_name',self.db.articles.find_one({'_id':'one'}))

    def test_historical_rewrites_disabled_without_redating_or_changing_text(self):
        published=self.now-timedelta(days=30)
        self.db.articles.insert_many([
            {'_id':'old','id':'old','slug':'old','status':'published','published_at':published,'body':'Original historical text','needs_gpt_rewrite':True},
            {'_id':'new','id':'new','slug':'new','status':'published','published_at':self.now-timedelta(hours=1),'needs_gpt_rewrite':True},
        ])
        apply(self.db,plan(self.db,self.now))
        old=self.db.articles.find_one({'_id':'old'})
        self.assertFalse(old['needs_gpt_rewrite'])
        self.assertEqual(old['rewrite_status'],'review')
        self.assertEqual(old['rewrite_review_reason'],'historical_content')
        self.assertEqual(utc_for_test(old['published_at']),published)
        self.assertEqual(old['body'],'Original historical text')
        self.assertTrue(self.db.articles.find_one({'_id':'new'})['needs_gpt_rewrite'])

    def seed_verified_players(self):
        self.db.players.insert_many([
            {'_id':'canonical-player','id':WIRTZ_KEEP,'slug':'wirtz','name':'Florian Wirtz','position':'Midfielder','current_club_id':WIRTZ_CLUB,'aliases':['Wirtz']},
            {'_id':'retired-player','id':WIRTZ_DUPLICATE,'slug':'florian-wirtz','name':'Florian Wirtz','position':'Midfielder','current_club_id':None},
        ])

    def test_verified_player_merge_remaps_all_known_references_and_archives_originals(self):
        self.seed_verified_players()
        self.db.articles.insert_one({'_id':'article','id':'article','slug':'fixture','linked_player_ids':[WIRTZ_DUPLICATE,WIRTZ_KEEP]})
        for collection in ('events','transfers','rumours','transfer_stories'):
            self.db[collection].insert_one({'_id':collection,'player_id':WIRTZ_DUPLICATE,'story_key':'fixture-story'})
        self.db.article_links.insert_one({'_id':'nested','links':[{'entity_type':'player','entity_id':WIRTZ_DUPLICATE}]})
        self.db.aliases.insert_one({'_id':'existing-alias','entity_type':'player','entity_id':WIRTZ_DUPLICATE,'normalized_alias':'wirtz-old'})
        operations=plan(self.db,self.now)
        self.assertEqual(self.db.players.count_documents({}),2)
        apply(self.db,operations)
        keeper=self.db.players.find_one({'id':WIRTZ_KEEP})
        self.assertEqual(self.db.players.count_documents({}),1)
        self.assertEqual(keeper['slug'],'wirtz')
        self.assertEqual(keeper['current_club_id'],WIRTZ_CLUB)
        self.assertIn('florian-wirtz',keeper['aliases'])
        self.assertEqual(self.db.articles.find_one()['linked_player_ids'],[WIRTZ_KEEP])
        for collection in ('events','transfers','rumours','transfer_stories'):
            self.assertEqual(self.db[collection].find_one()['player_id'],WIRTZ_KEEP)
        self.assertEqual(self.db.article_links.find_one()['links'][0]['entity_id'],WIRTZ_KEEP)
        self.assertEqual(self.db.aliases.find_one({'normalized_alias':'florian-wirtz'})['entity_id'],WIRTZ_KEEP)
        self.assertEqual(self.db.aliases.find_one({'normalized_alias':'wirtz-old'})['entity_id'],WIRTZ_KEEP)
        saved=self.db.repair_archive.find_one({'collection':'players','document.id':WIRTZ_DUPLICATE})
        self.assertEqual(saved['document']['slug'],'florian-wirtz')
        original=self.db.repair_archive.find_one({'collection':'articles'})['document']
        self.assertEqual(original['linked_player_ids'],[WIRTZ_DUPLICATE,WIRTZ_KEEP])
        self.assertEqual(self.db.repair_archive.count_documents({'collection':'aliases','document':None}),1)
        count=self.db.repair_archive.count_documents({})
        apply(self.db,plan(self.db,self.now))
        self.assertEqual(self.db.repair_archive.count_documents({}),count)

    def test_player_merge_aborts_on_unknown_reference_field_before_writes(self):
        self.seed_verified_players()
        self.db.legacy_links.insert_one({'opaque_reference':WIRTZ_DUPLICATE})
        with self.assertRaisesRegex(RuntimeError,'Unknown retired player ID reference'):
            plan(self.db,self.now)
        self.assertEqual(self.db.repair_archive.count_documents({}),0)
        self.assertEqual(self.db.players.count_documents({}),2)

    def test_player_merge_aborts_on_identity_conflict_and_alias_collision(self):
        self.seed_verified_players()
        self.db.players.update_one({'id':WIRTZ_DUPLICATE},{'$set':{'birthdate':'2000-01-01'}})
        with self.assertRaisesRegex(RuntimeError,'biographical'):
            plan(self.db,self.now)
        self.db.players.update_one({'id':WIRTZ_DUPLICATE},{'$unset':{'birthdate':''}})
        self.db.aliases.insert_one({'entity_type':'player','normalized_alias':'florian-wirtz','entity_id':'somebody-else'})
        with self.assertRaisesRegex(RuntimeError,'alias'):
            plan(self.db,self.now)
        self.assertEqual(self.db.repair_archive.count_documents({}),0)

    def test_player_merge_preflight_detects_new_alias_after_plan(self):
        self.seed_verified_players()
        operations=plan(self.db,self.now)
        self.db.aliases.insert_one({'entity_type':'player','normalized_alias':'florian-wirtz','entity_id':'somebody-else'})
        with self.assertRaisesRegex(RuntimeError,'source changed'):
            apply(self.db,operations)
        self.assertEqual(self.db.repair_archive.count_documents({}),0)


def utc_for_test(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


if __name__ == "__main__":
    unittest.main()

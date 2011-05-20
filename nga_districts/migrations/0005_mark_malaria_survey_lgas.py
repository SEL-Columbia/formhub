# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

from nga_districts.models import LGA

class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        unique_slugs_of_pilot_lgas = [
            "adamawa_song",
            "delta_ukwuani",
            "fct_kuje",
            "imo_nwangele",
            "jigawa_miga",
            "niger_wushishi",
            "ondo_akoko_north_east",
            ]
        unique_slugs_of_comparison_lgas = [
            "adamawa_fufore",
            "delta_bomadi",
            "fct_gwagwalada",
            "imo_orlu",
            "jigawa_biriniwa",
            "niger_katcha",
            "ondo_akoko_north_west",
            ]

        unique_slugs = unique_slugs_of_pilot_lgas + \
            unique_slugs_of_comparison_lgas

        qs = LGA.objects.filter(unique_slug__in=unique_slugs)
        qs.update(included_in_malaria_survey=True)


    def backwards(self, orm):
        "Write your backwards methods here."


    models = {
        'nga_districts.lga': {
            'Meta': {'object_name': 'LGA'},
            'afr_id': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'included_in_malaria_survey': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'kml_id': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'latlng_str': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'scale_up': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'state': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'lgas'", 'to': "orm['nga_districts.State']"}),
            'survey_round': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'unique_slug': ('django.db.models.fields.TextField', [], {'null': 'True'})
        },
        'nga_districts.state': {
            'Meta': {'object_name': 'State'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'zone': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'states'", 'to': "orm['nga_districts.Zone']"})
        },
        'nga_districts.zone': {
            'Meta': {'object_name': 'Zone'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'})
        }
    }

    complete_apps = ['nga_districts']

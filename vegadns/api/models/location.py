from builtins import object
from peewee import CharField, AutoField

from vegadns.api.models import database, BaseModel
from vegadns.api.models.location_prefix import LocationPrefix


class Location(BaseModel):
    location_id = AutoField()
    location = CharField(unique=True)
    location_description = CharField()

    class Meta(object):
        table_name = 'locations'

    def validate(self):
        location_len = len(self.location)
        if location_len < 1 or location_len > 2:
            raise ValueError(
                "location must be one or two characters in length"
            )

    def delete_prefixes(self):
        prefixes = LocationPrefix.select().where(
            LocationPrefix.location_id == self.location_id
        )

        for prefix in prefixes:
            prefix.delete_instance()

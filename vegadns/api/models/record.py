from builtins import object
import re

from peewee import IntegerField, CharField, AutoField

from vegadns.api.models import database, BaseModel, ensure_validation
import vegadns.api.models.recordtypes


class Record(BaseModel):
    distance = IntegerField(null=True, default=0)
    domain_id = IntegerField(column_name='domain_id')
    host = CharField()
    port = IntegerField(null=True)
    record_id = AutoField()
    ttl = IntegerField()
    location_id = IntegerField(null=True, default=None)
    type = CharField(null=True)
    val = CharField(null=True)
    weight = IntegerField(null=True)

    def to_recordtype(self):
        instance = vegadns.api.models.recordtypes.AbstractRecordType.singleton(
            self
        )
        instance.from_model(self)
        return instance

    class Meta(object):
        table_name = 'records'

    def validate(self):
        recordtype = self.to_recordtype()
        recordtype.validate()

    @staticmethod
    def hostname_in_domain(hostname, domain):
        p = re.compile("(.*[.])?" + domain + "([.])?$", re.IGNORECASE)
        m = p.match(hostname)
        return bool(m)

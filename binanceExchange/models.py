from django.db import models

# Create your models here.
from django.db import models

# Create your models here.


class Symbol(models.Model):
    sym_name = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    users = models.ManyToManyField('auth.User', related_name='symbols')
    min_qty = models.FloatField(default=0.001)
    step_size = models.FloatField(default=0.001)
    def __str__(self):
        return self.sym_name



class SizeConfig(models.Model):
    margin = models.FloatField()
    trade_wallet_percent = models.FloatField()
    leverage = models.IntegerField()

    def save(self, *args, **kwargs):
        # if SizeConfig.objects.count() > 0:
        #     raise Exception('Only one SizeConfig instance is allowed')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Margin:{self.margin}, Percent:{self.trade_wallet_percent} Leverage:{self.leverage}'

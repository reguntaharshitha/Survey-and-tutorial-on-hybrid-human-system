from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered
from .models import TrustMetric, EthicalAlignment, MutualTrust
from django.utils.html import format_html


class TrustMetricAdmin(admin.ModelAdmin):
	list_display = ('user', 'metric_type', 'value', 'confidence', 'timestamp')
	list_filter = ('metric_type',)
	search_fields = ('user__username',)
	readonly_fields = ('timestamp',)


class EthicalAlignmentAdmin(admin.ModelAdmin):
	list_display = ('user', 'principle', 'alignment_score', 'timestamp')
	search_fields = ('user__username', 'principle')
	readonly_fields = ('timestamp',)


class MutualTrustAdmin(admin.ModelAdmin):
	list_display = ('user', 'mutual_trust_score', 'timestamp')
	readonly_fields = ('timestamp',)


# Avoid double-registration if another app already registered these models
for model, admin_class in (
	(TrustMetric, TrustMetricAdmin),
	(EthicalAlignment, EthicalAlignmentAdmin),
	(MutualTrust, MutualTrustAdmin),
):
	try:
		admin.site.register(model, admin_class)
	except AlreadyRegistered:
		# model already registered elsewhere (e.g., admin_management); skip
		pass

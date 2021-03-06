import datetime

import tenders.runner
from tenders.models import *


class Runner(tenders.runner.Runner):


	name  = 'Zakupki.gov.ru FZ44'
	alias = 'fz44'

	black_list = ['_logs', 'fcs_undefined', 'auditresult', 'customerreports', 'regulationrules', 'requestquotation', 'dygeja_Resp']

	categories = {
		'essences' : 'fcs_nsi',
		'regions'  : 'fcs_regions'}

	subcategories = [
		None,
		'prevMonth',
		'currMonth']


	def __init__(self):

		super().__init__()

		self.max_time = datetime.timedelta(0, 60*60*23, 0)

		self.url = 'ftp.zakupki.gov.ru'

		self.essences = [
			{'category' : 'nsiOKSM',                           'parser' : self.parse_country},
			{'category' : 'nsiCurrency',                       'parser' : self.parse_currency},
			{'category' : 'nsiContractCurrencyCBRF',           'parser' : self.parse_currency},
			{'category' : 'nsiOKEI',                           'parser' : self.parse_okei},
			{'category' : 'nsiKOSGU',                          'parser' : self.parse_kosgu},
			{'category' : 'nsiOKOPF',                          'parser' : self.parse_okopf},
			{'category' : 'nsiOKPD',                           'parser' : self.parse_okpd},
			{'category' : 'nsiOKPD2',                          'parser' : self.parse_okpd2},
			{'category' : 'nsiOKTMO',                          'parser' : self.parse_oktmo},
			{'category' : 'nsiOKVED',                          'parser' : self.parse_okved},
			{'category' : 'nsiOKVED2',                         'parser' : self.parse_okved2},
			{'category' : 'nsiBudget',                         'parser' : self.parse_budget},
			{'category' : 'nsiOffBudgetType',                  'parser' : self.parse_budget_type},
			{'category' : 'nsiOrganizationType',               'parser' : self.parse_organisation_type},
			{'category' : 'nsiOrganization',                   'parser' : self.parse_organisation},
			{'category' : 'nsiPlacingWay',                     'parser' : self.parse_placingway},
			{'category' : 'nsiPlanPositionChangeReason',       'parser' : self.parse_plan_position_change_reason},
#			{'category' : 'nsiContractModificationReason',     'parser' : self.parse_contract_modification_reason},

#			{'category' : 'nsiPurchaseDocumentTypes',          'parser' : self.parse_},
#			{'category' : 'nsiPurchasePreferences',            'parser' : self.parse_},
#			{'category' : 'nsiPurchaseRejectReason',           'parser' : self.parse_},

#			{'category' : 'fcsStandardContract',               'parser' : self.parse_},
#			{'category' : 'fcsStandardContractInvalid',        'parser' : self.parse_},
#			{'category' : 'nsiAbandonedReason',                'parser' : self.parse_},
#			{'category' : 'nsiAuditActionSubjects',            'parser' : self.parse_},
#			{'category' : 'nsiBankGuaranteeRefusalReason',     'parser' : self.parse_},
#			{'category' : 'nsiBusinessControls',               'parser' : self.parse_},
#			{'category' : 'nsiCalendarDays',                   'parser' : self.parse_},
#			{'category' : 'nsiCommission',                     'parser' : self.parse_},
#			{'category' : 'nsiCommissionRole',                 'parser' : self.parse_},
#			{'category' : 'nsiContractExecutionDoc',           'parser' : self.parse_},
#			{'category' : 'nsiContractOKOPFExtraBudget',       'parser' : self.parse_},
#			{'category' : 'nsiContractPenaltyReason',          'parser' : self.parse_},
#			{'category' : 'nsiContractPriceChangeReason',      'parser' : self.parse_},
#			{'category' : 'nsiContractRefusalReason',          'parser' : self.parse_},
#			{'category' : 'nsiContractReparationDoc',          'parser' : self.parse_},
#			{'category' : 'nsiContractSingleCustomerReason',   'parser' : self.parse_},
#			{'category' : 'nsiContractTerminationReason',      'parser' : self.parse_},
#			{'category' : 'nsiDeviationFactFoundation',        'parser' : self.parse_},
#			{'category' : 'nsiEvalCriterion',                  'parser' : self.parse_},
#			{'category' : 'nsiModifyReasonOZ',                 'parser' : self.parse_},
#			{'category' : 'nsiPublicDiscussionDecisions',      'parser' : self.parse_},
#			{'category' : 'nsiPublicDiscussionQuestionnaries', 'parser' : self.parse_},
#			{'category' : 'nsiSingleCustomerReasonOZ',         'parser' : self.parse_},
#			{'category' : 'nsiSpecialPurchase',                'parser' : self.parse_},

#			{'category' : 'nsiOrganizationRights',             'parser' : self.parse_},
		]

		self.region_essences = [
			{'category' : 'notifications', 'parser' : self.parse_notification},
			{'category' : 'plangraphs',    'parser' : self.parse_plan},
		]


	def run(self):


		if not self.updater.login or not self.updater.password:
			print('Ошибка: Проверьте параметры авторизации. Кажется их нет.')
			return False

		print('Обновляем справочники')
		for essence in self.essences:

			print('\n\n{}'.format(essence['category']))

			# Проверяем не вышло ли время
			if self.is_time_up():
				return True

			self.update_essence(essence)


		print('Обновляем данные с регионов')

		for essence in self.region_essences:

			print('\n\n{}'.format(essence['category']))

			for region_key in self.get_ftp_catalog(self.url, self.categories['regions']):

				if (not region_key in self.black_list) and (not '.'in region_key):
					try:
						self.get_ftp_catalog(self.url, '{}/{}'.format(self.categories['regions'], region_key))
						region = Region.objects.get_by_key(
							updater = updater,
							ext_key = region_key)
						print(region)
	
					except Exception:
						continue

					if region and region.state:

						for essence in self.region_essences:

							if self.is_time_up():
								return True

							self.update_region_essence(region, essence)

		print("Завершил за {}.".format(timezone.now() - self.start_time))
		return True


	def update_essence(self, essence):
		'Получает файлы сущностей для анализа и обработки'

		catalog = "{}/{}".format(self.categories['essences'], essence['category'])

		zip_names = self.get_ftp_catalog(self.url, catalog)

		# Загружаем архивы
		for zip_name in zip_names:

			# Проверяем, не вышло ли время
			if self.is_time_up():
				return True

			# Проверяем, не обработан ли файл
			source = Source.objects.take(url = "{}/{}/{}".format(self.url, catalog, zip_name))
			if source.is_parsed():
				continue

			# Скачиваем архив
			zip_data = self.get_file_from_ftp(self.url, catalog, zip_name)

			if not zip_data:
				continue

			# Проходим по всем файлам в архиве
			for xml_name in zip_data.namelist():

				# Извлекаем данные
				tree = self.get_tree_from_zip(zip_data, xml_name)
				if tree:
					tree = self.clear_tags(tree)
				else:
					continue

				# Обрабатываем файл
				parse = essence['parser']
				parse(tree)

			source.complite(updater = self.updater)

		return True


	def update_region_essence(self, region, essence):
		'Получает файлы сущностей для анализа и обработки'

		for subcategory in self.subcategories:

			if subcategory:
				catalog = "{}/{}/{}/{}".format(self.categories['regions'], region.alias, essence['category'], subcategory)
			else:
				catalog = "{}/{}/{}".format(self.categories['regions'], region.alias, essence['category'])	

			zip_names = self.get_ftp_catalog(self.url, catalog)

			# Загружаем архивы
			for zip_name in zip_names:

				# Проверяем, не вышло ли время
				if self.is_time_up():
					return True

				# Проверяем, не обработан ли файл
				source = Source.objects.take(url = "{}/{}/{}".format(self.url, catalog, zip_name))
				if source.is_parsed():
					continue

				# Скачиваем архив
				zip_data = self.get_file_from_ftp(self.url, catalog, zip_name)

				if not zip_data:
					continue

				# Проходим по всем файлам в архиве
				for xml_name in zip_data.namelist():

					# Извлекаем данные
					tree = self.get_tree_from_zip(zip_data, xml_name)
					if tree:
						tree = self.clear_tags(tree)
					else:
						continue

					# Обрабатываем файл
					parse = essence['parser']
					parse(tree, region)

				source.complite(updater = self.updater)

		return True


	def parse_country(self, tree):

		for element in tree.xpath('.//nsiOKSM'):

			country = Country.objects.write(
				code         = self.get_text(element, './countryCode'),
				full_name    = self.get_text(element, './countryFullName'),
				state        = self.get_bool(element, './actual'))

			print("Страна: {}.".format(country))


	def parse_currency(self, tree):

		for element in tree.xpath('.//nsiCurrency'):

			currency = Currency.objects.write(
				code         = self.get_text(element, './code'),
				digital_code = self.get_text(element, './digitalCode'),
				name         = self.get_text(element, './name'),
				state        = self.get_bool(element, './actual'))

			print("Валюта: {}.".format(currency))

		for element in tree.xpath('.//currency'):

			currency = Currency.objects.write(
				code         = self.get_text(element, './code'),
				digital_code = self.get_text(element, './digitalCode'),
				name         = self.get_text(element, './name'))

			print("Валюта: {}.".format(currency))


	def parse_okei(self, tree):

		for element in tree.xpath('.//nsiOKEI'):

			okei_section = OKEISection.objects.take(
				code  = self.get_text(element, './section/code'),
				name  = self.get_text(element, './section/name'),
				state = True)

			okei_group = OKEIGroup.objects.take(
				code  = self.get_text(element, './group/id'),
				name  = self.get_text(element, './group/name'),
				state = True)

			okei = OKEI.objects.write(
				code                 = self.get_text(element, './code'),
				name                 = self.get_text(element, './fullName'),
				section              = okei_section,
				group                = okei_group,
				local_name           = self.get_text(element, './localName'),
				international_name   = self.get_text(element, './internationalName'),
				local_symbol         = self.get_text(element, './localSymbol'),
				international_symbol = self.get_text(element, './internationalSymbol'),
				state                = self.get_bool(element, './actual'))
			print("Единица измерения: {}.".format(okei))


	def parse_kosgu(self, tree):
		'Парсит классификатор операций сектора государственного управления.'
		for element in tree.xpath('.//nsiKOSGU'):

			code = self.get_text(element, './parentCode')
			if code == '000' or not code:
				code = None
			parent = KOSGU.objects.take(code = code)

			kosgu = KOSGU.objects.write(
				code   = self.get_text(element, './code'),
				parent = parent,
				name   = self.get_text(element, './name'),
				state  = self.get_bool(element, './actual'))

			print("КОСГУ: {}.".format(kosgu))


	def parse_okopf(self, tree):

		for element in tree.xpath('.//nsiOKOPF'):

			parent = OKOPF.objects.take(code = self.get_text(element, './parentCode'))

			okopf = OKOPF.objects.write(
				code          = self.get_text(element, './code'),
				full_name     = self.get_text(element, './fullName'),
				singular_name = self.get_text(element, './singularName'),
				parent        = parent,
				state         = self.get_bool(element, './actual'))

			print("ОКОПФ: {}.".format(okopf))


	def parse_okpd(self, tree):

		for element in tree.xpath('.//nsiOKPD'):

			parent = OKPD.objects.get_by_key(
				updater = self.updater,
				key     = self.get_text(element, './parentId'))

			okpd = OKPD.objects.write(
				parent = parent,
				code   = self.get_text(element, './code'),
				name   = self.get_text(element, './name'),
				state  = self.get_bool(element, './actual'))

			key = OKPDKey.objects.write(
				updater = self.updater,
				key     = self.get_text(element, './id'),
				okpd    = okpd)

			print("ОКПД: {}.".format(okpd))


	def parse_okpd2(self, tree):

		for element in tree.xpath('.//nsiOKPD2'):

			parent = OKPD2.objects.get_by_key(
				updater = self.updater,
				key     = self.get_text(element, './parentId'))

			okpd2 = OKPD2.objects.write(
				parent = parent,
				code   = self.get_text(element, './code'),
				name   = self.get_text(element, './name'),
				state  = self.get_bool(element, './actual'))

			key = OKPD2Key.objects.write(
				updater = self.updater,
				key     = self.get_text(element, './id'),
				okpd2   = okpd2)

			print("ОКПД2: {}.".format(okpd2))


	def parse_oktmo(self, tree):

		for element in tree.xpath('.//nsiOKTMO'):

			parent = OKTMO.objects.take(code = self.get_text(element, './parentCode'))

			oktmo = OKTMO.objects.write(
				code   = self.get_text(element, './code'),
				parent = parent,
				name   = self.get_text(element, './fullName'))

			print("ОКТМО: {}.".format(oktmo))


	def parse_okved(self, tree):

		for element in tree.xpath('.//nsiOKVED'):

			section    = OKVEDSection.objects.take(name = self.get_text(element, './section'))
			subsection = OKVEDSubSection.objects.take(name = self.get_text(element, './subsection'))

			parent = OKVED.objects.get_by_key(
				updater = self.updater,
				key     = self.get_text(element, './parentId'))

			okved = OKVED.objects.write(
				code       = self.get_text(element, './code'),
				section    = section,
				subsection = subsection,
				parent     = parent,
				name       = self.get_text(element, './name'),
				state      = self.get_bool(element, './actual'))

			key = OKVEDKey.objects.write(
				updater = self.updater,
				key     = self.get_text(element, './id'),
				okved   = okved)

			print("ОКВЭД: {}.".format(okved))


	def parse_okved2(self, tree):

		for element in tree.xpath('.//nsiOKVED2'):

			section = OKVED2Section.objects.take(name = self.get_text(element, './section'))
			parent  = OKVED2.objects.take(code = self.get_text(element, './parentCode'))

			okved2 = OKVED2.objects.write(
				code       = self.get_text(element, './code'),
				section    = section,
				parent     = parent,
				name       = self.get_text(element, './name'),
				comment    = self.get_text(element, './comment'),
				state      = self.get_bool(element, './actual'))

			key = OKVED2Key.objects.write(
				updater = self.updater,
				key     = self.get_text(element, './id'),
				okved2  = okved2)

			print("ОКВЭД2: {}.".format(okved2))


	def parse_budget(self, tree):

		for element in tree.xpath('.//nsiBudget'):

			budget = Budget.objects.write(
				code       = self.get_text(element, './code'),
				name       = self.get_text(element, './name'),
				state      = self.get_bool(element, './actual'))

			print("Бюджет: {}.".format(budget))


	def parse_budget_type(self, tree):

		for element in tree.xpath('.//nsiOffBudget'):

			subsystem_type = SubsystemType.objects.take(code = self.get_text(element, './subsystemType'))

			budget_type = BudgetType.objects.write(
				code           = self.get_text(element, './code'),
				name           = self.get_text(element, './name'),
				subsystem_type = subsystem_type,
				state          = self.get_bool(element, './actual'))
			print("Тип бюджета: {}.".format(budget_type))


	def parse_organisation_type(self, tree):

		for element in tree.xpath('.//nsiOrganizationType'):

			organisation_type = OrganisationType.objects.write(
				code        = self.get_text(element, './code'),
				name        = self.get_text(element, './name'),
				description = self.get_text(element, './description'))

			print("Тип организации: {}".format(organisation_type))


	def parse_organisation(self, tree):

		for element in tree.xpath('.//nsiOrganization'):

			factual_address = Address.objects.take(address = self.get_text(element, './factualAddress/addressLine'))
			postal_address  = Address.objects.take(address = self.get_text(element, './postalAddress'))

			email = Email.objects.take(email = self.get_text(element, './email'))
			phone = Phone.objects.take(phone = self.get_text(element, './phone'))
			fax   = Phone.objects.take(phone = self.get_text(element, './fax'))

			contact_person = Person.objects.take(
				first_name  = self.get_text(element, './contactPerson/firstName'),
				middle_name = self.get_text(element, './contactPerson/middleName'),
				last_name   = self.get_text(element, './contactPerson/lastName'),
				email       = email,
				phone       = phone,
				fax         = fax)

			head_agency = Organisation.objects.get_by_key(
				updater = self.updater,
				key     = self.get_text(element, './headAgency/regNum'))

			ordering_agency = Organisation.objects.get_by_key(
				updater = self.updater,
				key     = self.get_text(element, './orderingAgency/regNum'))

			okopf = OKOPF.objects.take(
				code      = self.get_text(element, './OKOPF/code'),
				full_name = self.get_text(element, './OKOPF/fullName'))

			okogu = OKOGU.objects.take(
				code = self.get_text(element, './OKOGU/code'),
				name = self.get_text(element, './OKOGU/name'))

			organisation_role = OrganisationRole.objects.take(
				code = self.get_text(element, './organizationRole'))

			organisation_type = OrganisationType.objects.take(
				code = self.get_text(element, './organizationType/code'),
				name = self.get_text(element, './organizationType/name'))

			oktmo = OKTMO.objects.take(
				code = self.get_text(element, './OKTMO/code'))

			organisation = Organisation.objects.write(
				inn               = self.get_text(element, './INN'),
				kpp               = self.get_text(element, './KPP'),
				short_name        = self.get_text(element, './shortName'),
				full_name         = self.get_text(element, './fullName'),
				ogrn              = self.get_text(element, './OGRN'),
				okpo              = self.get_text(element, './OKPO'),
				factual_address   = factual_address,
				postal_address    = postal_address,
				email             = email,
				phone             = phone,
				fax               = fax,
				contact_person    = contact_person,
				head_agency       = head_agency,
				ordering_agency   = ordering_agency,
				okopf             = okopf,
				okogu             = okogu,
				organisation_role = organisation_role,
				organisation_type = organisation_type,
				oktmo             = oktmo,
				state             = self.get_bool(element, './actual'),
				register          = self.get_bool(element, './register'))

			key = OrganisationKey.objects.write(
				updater      = self.updater,
				key          = self.get_text(element, './regNumber'),
				organisation = organisation)

			print('Организация: {}'.format(organisation))


	def parse_placingway(self, tree):

		for element in tree.xpath('.//nsiPlacingWay'):

			subsystem_type = SubsystemType.objects.take(
				code = self.get_text(element, './subsystemType'))

			placingway = PlacingWay.objects.write(
				code           = self.get_text(element, './code'),
				name           = self.get_text(element, './name'),
				type_code      = self.get_text(element, './type'),
				subsystem_type = subsystem_type,
				state          = self.get_bool(element, './actual'))

			key = PlacingWayKey.objects.write(
				updater    = self.updater,
				key        = self.get_text(element, './placingWayId'),
				placingway = placingway)

			print(placingway)

		return True


	def parse_plan_position_change_reason(self, tree):

		for element in tree.xpath('.//nsiPlanPositionChangeReason'):

			changereason = PlanPositionChangeReason.objects.write(
					name        = self.get_text(element, './name'),
					description = self.get_text(element, './description'),
					state       = self.get_bool(element, './actual'))

			key = PlanPositionChangeReasonKey.objects.write(
				updater                  = self.updater,
				key                      = self.get_text(element, './id'),
				planpositionchangereason = changereason)

			print(changereason)

		return True


	def parse_contract_modification_reason(self, tree):

		for element in tree.xpath('.//nsiContractModificationReason/nsiContractModificationReason'):

			o = ContractModificationReason.objects.write(
				code  = self.get_text(element, './code'),
				name  = self.get_text(element, './name'),
				state = self.get_bool(element, './actual'))

			print(o)

		return True


	def parse_plan(self, tree, region):
		'Парсит планы-графики.'

		for element in tree.xpath('.//tenderPlanCancel'):

			customer = OrganisationExtKey.objects.get_organisation(
				updater = self.updater,
				ext_key = self.get_text(element, './customerInfo/regNum'))

			plan = Plan.objects.write(
				number         = self.get_text(element, './planNumber'),
				version        = self.get_text(element, './versionNumber'),
				year           = self.get_text(element, './year'),
				description    = self.get_text(element, './description'),
				url            = self.get_text(element, './printForm/url'),
				created        = self.get_text(element, './cancelDate'),
				region         = region,
				customer       = customer,
				state          = False)

			ext_key = PlanExtKey.objects.write(
				updater = self.updater,
				ext_key = self.get_text(element, './id'),
				plan = plan)

			print('Отменён: {}.'.format(plan.number))


		for element in tree.xpath('.//tenderPlanUnstructured'):

			owner = OrganisationExtKey.objects.get_organisation(
				updater = self.updater,
				ext_key = self.get_text(element, './commonInfo/owner/regNum'))

			customer = OrganisationExtKey.objects.get_organisation(
				updater = self.updater,
				ext_key = self.get_text(element, './customerInfo/customer/regNum'))

			email = Email.objects.take(email = self.get_text(element, './responsibleContactInfo/email'))
			phone = Phone.objects.take(phone = self.get_text(element, './responsibleContactInfo/phone'))
			fax   = Phone.objects.take(phone = self.get_text(element, './responsibleContactInfo/fax'))

			contact_person = Person.objects.take(
				first_name  = self.get_text(element, './responsibleContactInfo/firstName'),
				middle_name = self.get_text(element, './responsibleContactInfo/middleName'),
				last_name   = self.get_text(element, './responsibleContactInfo/lastName'),
				email       = email,
				phone       = phone,
				fax         = fax)

			plan = Plan.objects.write(
				number         = self.get_text(element, './commonInfo/planNumber'),
				version        = self.get_text(element, './commonInfo/versionNumber'),
				year           = self.get_text(element, './commonInfo/year'),
				description    = self.get_text(element, './commonInfo/description'),
				url            = self.get_text(element, './printForm/url'),
				created        = self.get_text(element, './commonInfo/createDate'),
				confirmed      = self.get_text(element, './commonInfo/confirmDate'),
				published      = self.get_text(element, './commonInfo/publishDate'),
				region         = region,
				owner          = owner,
				customer       = customer,
				contact_person = contact_person)

			ext_key = PlanExtKey.objects.write(
				updater = self.updater,
				ext_key = self.get_text(element, './commonInfo/id'),
				plan = plan)

			print('{} - unstructured.'.format(plan.number))


		for element in tree.xpath('.//tenderPlan'):

			owner = OrganisationExtKey.objects.get_organisation(
				updater = self.updater,
				ext_key = self.get_text(element, './commonInfo/owner/regNum'))

			customer = OrganisationExtKey.objects.get_organisation(
				updater = self.updater,
				ext_key = self.get_text(element, './customerInfo/customer/regNum'))

			email = Email.objects.take(email = self.get_text(element, './responsibleContactInfo/email'))
			phone = Phone.objects.take(phone = self.get_text(element, './responsibleContactInfo/phone'))
			fax   = Phone.objects.take(phone = self.get_text(element, './responsibleContactInfo/fax'))

			contact_person = Person.objects.take(
				first_name  = self.get_text(element, './responsibleContactInfo/firstName'),
				middle_name = self.get_text(element, './responsibleContactInfo/middleName'),
				last_name   = self.get_text(element, './responsibleContactInfo/lastName'),
				email       = email,
				phone       = phone,
				fax         = fax)

			plan = Plan.objects.write(
					number         = self.get_text(element, './commonInfo/planNumber'),
					version        = self.get_text(element, './commonInfo/versionNumber'),
					year           = self.get_text(element, './commonInfo/year'),
					description    = self.get_text(element, './commonInfo/description'),
					url            = self.get_text(element, './printForm/url'),
					created        = self.get_text(element, './commonInfo/createDate'),
					confirmed      = self.get_text(element, './commonInfo/confirmDate'),
					published      = self.get_text(element, './commonInfo/publishDate'),
					region         = region,
					owner          = owner,
					customer       = customer,
					contact_person = contact_person)

			ext_key = PlanExtKey.objects.write(
				updater = self.updater,
				ext_key = self.get_text(element, './commonInfo/id'),
				plan = plan)


			print('{} {}.'.format(plan.number, plan))

			for pos in element.xpath('.//positions/position'):

				currency = Currency.objects.take(code = self.get_text(pos, './commonInfo/contractCurrency/code'))
				placing_way = PlacingWay.objects.take(code = self.get_text(pos, './commonInfo/placingWay/code'))

				change_reason = PlanPositionChangeReasonExtKey.objects.get_change_reason(
					updater = self.updater,
					ext_key = self.get_text(pos, './commonInfo/positionModification/changeReason/id'))

				position = PlanPosition.objects.write(
					plan            = plan,
					number          = self.get_text(pos, './commonInfo/positionNumber'),
					name            = self.get_text(pos, './commonInfo/contractSubjectName'),
					purchase_month  = self.get_int(pos, './purchaseConditions/purchaseGraph/purchasePlacingTerm/month'),
					purchase_year   = self.get_int(pos, './purchaseConditions/purchaseGraph/purchasePlacingTerm/year'),
					execution_month = self.get_int(pos, './purchaseConditions/purchaseGraph/contractExecutionTerm/month'),
					execution_year  = self.get_int(pos, './purchaseConditions/purchaseGraph/contractExecutionTerm/year'),
					max_price       = self.get_float(pos, './commonInfo/contractMaxPrice'),
					currency        = currency,
					placing_way     = placing_way,
					change_reason   = change_reason)

				position.okveds.clear()
				for okv in pos.xpath('.//OKVEDs/OKVED'):
					okved = OKVED.objects.take(code = self.get_text(okv, './code'))

					if okved:
						link = PlanPositionToOKVED()
						link.plan_position = position
						link.okved         = okved
						link.save()

				position.okveds2.clear()
				for okv2 in pos.xpath('.//OKVEDs/OKVED2'):
					okved2 = OKVED2.objects.take(code = self.get_text(okv2, './code'))
					if okved2:
						link = PlanPositionToOKVED2()
						link.plan_position = position
						link.okved2        = okved2
						link.save()

				position.products.clear()
				for prod in pos.xpath('.//products/product'):

					okpd    = OKPD.objects.take(code = self.get_text(prod, './OKPD/code'))
					okpd2   = OKPD2.objects.take(code = self.get_text(prod, './OKPD2/code'))
					product = Product.objects.take(okpd = okpd, okpd2 = okpd2, name = self.get_text(prod, './name'))
					okei    = OKEI.objects.take(code = self.get_text(prod, './OKEI/code'))

					link = PlanPositionToProduct()
					link.plan_position = position
					link.product       = product
					link.requirement   = self.get_text(prod, './minRequirement')
					link.quantity      = self.get_float(prod, './quantity')
					link.price         = self.get_float(prod, './price')
					link.total         = self.get_float(prod, './sumMax')
					link.okei          = okei
					link.save()


	# TODO
	def parse_notification(self, tree, region):
		'Парсит извещения.'

		# TODO KILL
		import xml.etree.ElementTree as ET
#		print('parse_notification')
#		print(ET.tostring(tree.getroot(), encoding = 'unicode'))
		ok = False



		# Запрос котировок
		for element in tree.xpath('//fcsNotificationZK'):
			ok = self.parse_notification_tender(element, region)

		# Запрос котировок в целях оказания гуманитарной помощи либо ..
		for element in tree.xpath('//fcsNotificationZKBI'):
			ok = self.parse_notification_tender(element, region)

		# Закупка у единственного поставщика (подрядчика, исполнителя)
		for element in tree.xpath('//fcsNotificationEP'):
			ok = self.parse_notification_tender(element, region)

		# Электронный аукцион
		for element in tree.xpath('//fcsNotificationEF'):
			ok = self.parse_notification_tender(element, region)

		# Открытый конкурс
		for element in tree.xpath('//fcsNotificationOK'):
			ok = self.parse_notification_tender(element, region)

		# Двухэтапный конкурс
		for element in tree.xpath('//fcsNotificationOKD'):
			ok = self.parse_notification_tender(element, region)

		# Конкурс с ограниченным участием
		for element in tree.xpath('//fcsNotificationOKOU'):
			ok = self.parse_notification_tender(element, region)

		# Запрос предложений
		for element in tree.xpath('//fcsNotificationZP'):
			ok = self.parse_notification_tender(element, region)

		# Запрос котировок без размещения извещения
		for element in tree.xpath('//fcsNotificationISO'):
			ok = self.parse_notification_tender(element, region)

		# Конкурс с ограниченным участием
		for element in tree.xpath('//fcsNotificationISM'):
			ok = self.parse_notification_tender(element, region)

		# Предварительный отбор
		for element in tree.xpath('//fcsNotificationPO'):
			ok = self.parse_notification_tender(element, region)

		for element in tree.xpath('//fcsNotificationZakKOU'):
			self.parse_notification_tender(element, region)

		# Изменение лота
		for element in tree.xpath('//fcsNotificationLotChange'):
			ok = self.parse_notification_lot_change(element, region)

		# Продление закупки
		for element in tree.xpath('//fcsPurchaseProlongationZK'):
			ok = self.parse_notification_tender_prolongation(element, region)

		# Продление срока рассмотрения заявок
		for element in tree.xpath('//fcsPurchaseProlongationOK'):
			ok = self.parse_notification_tender_prolongation(element, region)

		# Отмена закупки
		for element in tree.xpath('//fcsNotificationCancel'):
			ok = self.parse_notification_tender_cancel(element, region)

		for element in tree.xpath('//fcsNotificationLotCancel'):
			self.parse_notification_lot_cancel(element, region)

		# Подписание контракта
		for element in tree.xpath('//fcsContractSign'):
			ok = self.parse_notification_sign(element, region)

		# Добавление документа
		for element in tree.xpath('//fcsPurchaseDocument'):
			ok = self.parse_notification_document(element, region)

		# Добавление ответа
		for element in tree.xpath('//fcsClarification'):
			ok = self.parse_notification_document(element, region)

		# Добавление протокола
		for element in tree.xpath('//fcsProtocolZKBI'):
			ok = self.parse_notification_protocol(element, region)


		if not ok:
			print(ET.tostring(tree.getroot(), encoding = 'unicode'))
			exit()




	def parse_notification_tender(self, element, region):

		responsible = OrganisationExtKey.objects.get_organisation(
			updater = self.updater,
			ext_key = self.get_text(element, './purchaseResponsible/responsibleOrg/regNum'))

		specialised = OrganisationExtKey.objects.get_organisation(
			updater = self.updater,
			ext_key = self.get_text(element, './purchaseResponsible/specializedOrg/regNum'))

		# TODO TEST
		import xml.etree.ElementTree as ET
		if not responsible:
			print(ET.tostring(element, encoding = 'unicode'))
			print('Ответственного нет!!!')
			return False

		email = Email.objects.take(email = self.get_text(element, './purchaseResponsible/responsibleInfo/contactEMail'))
		phone = Phone.objects.take(phone = self.get_text(element, './purchaseResponsible/responsibleInfo/contactPhone'))

		contact_person = Person.objects.take(
			first_name  = self.get_text(element, './purchaseResponsible/responsibleInfo/contactPerson/firstName'),
			middle_name = self.get_text(element, './purchaseResponsible/responsibleInfo/contactPerson/middleName'),
			last_name   = self.get_text(element, './purchaseResponsible/responsibleInfo/contactPerson/lastName'),
			email       = email,
			phon        = phone)

		placing_way = PlacingWay.objects.take(code = self.get_text(element, './placingWay/code'))

		etp = ETP.objects.take(
			code = self.get_text(element, './ETP/code'),
			name = self.get_text(element, './ETP/name'),
			url  = self.get_text(element, './ETP/url'))

		purchase = Purchase.objects.write(
			number                 = self.get_text(element, './purchaseNumber'),
			name                   = self.get_text(element, './purchaseObjectInfo'),
			url                    = self.get_text(element, './href'),
			published              = self.get_datetime(element, './docPublishDate'),
			region                 = region,
			responsible            = responsible,
			specialised            = specialised,
			contact_person         = contact_person,
			placing_way            = placing_way,

			grant_place            = Address.objects.take(address = self.get_text(element, './purchaseDocumentation/grantPlace')),
			collecting_place       = Address.objects.take(address = self.get_text(element, './procedureInfo/collecting/place')),
			opening_place          = Address.objects.take(address = self.get_text(element, './procedureInfo/opening/place')),
			final_opening_place    = Address.objects.take(address = self.get_text(element, './procedureInfo/finalOpening/place')),
			prequalification_place = Address.objects.take(address = self.get_text(element, './procedureInfo/prequalification/place')),
			selecting_place        = Address.objects.take(address = self.get_text(element, './procedureInfo/selecting/place')),
			scoring_place          = Address.objects.take(address = self.get_text(element, './procedureInfo/scoring/place')),

			collecting_st1_place   = Address.objects.take(address = self.get_text(element, './procedureInfo/stageOne/collecting/place')),
			opening_st1_place      = Address.objects.take(address = self.get_text(element, './procedureInfo/stageOne/opening/place')),
			scoring_st1_place      = Address.objects.take(address = self.get_text(element, './procedureInfo/stageOne/scoring/place')),

			collecting_st2_place   = Address.objects.take(address = self.get_text(element, './procedureInfo/stageTwo/collecting/place')),
			opening_st2_place      = Address.objects.take(address = self.get_text(element, './procedureInfo/stageTwo/opening/place')),
			scoring_st2_place      = Address.objects.take(address = self.get_text(element, './procedureInfo/stageTwo/scoring/place')),

			etp                    = etp,

			grant_start_time       = self.get_datetime(element, './purchaseDocumentation/grantStartDate'),
			grant_end_time         = self.get_datetime(element, './purchaseDocumentation/grantEndDate'),

			collecting_start_time  = self.get_datetime(element, './procedureInfo/collecting/startDate'),
			collecting_end_time    = self.get_datetime(element, './procedureInfo/collecting/endDate'),
			opening_time           = self.get_datetime(element, './procedureInfo/opening/date'),
			final_opening_time     = self.get_datetime(element, './procedureInfo/finalOpening/date'),
			prequalification_time  = self.get_datetime(element, './procedureInfo/prequalification/date'),
			selecting_time         = self.get_datetime(element, './procedureInfo/selecting/date'),
			scoring_time           = self.get_datetime(element, './procedureInfo/scoring/date'),
			bidding_time           = self.get_datetime(element, './procedureInfo/bidding/date'),

			collecting_st1_start_time  = self.get_datetime(element, './procedureInfo/stageOne/collecting/startDate'),
			collecting_st1_end_time    = self.get_datetime(element, './procedureInfo/stageOne/collecting/endDate'),
			opening_st1_time           = self.get_datetime(element, './procedureInfo/stageOne/opening/date'),
			scoring_st1_time           = self.get_datetime(element, './procedureInfo/stageOne/scoring/date'),
			collecting_st2_start_time  = self.get_datetime(element, './procedureInfo/stageTwo/collecting/startDate'),
			collecting_st2_end_time    = self.get_datetime(element, './procedureInfo/stageTwo/collecting/endDate'),
			opening_st2_time           = self.get_datetime(element, './procedureInfo/stageTwo/opening/date'),
			scoring_st2_time           = self.get_datetime(element, './procedureInfo/stageTwo/scoring/date'))


		print('{} - added'.format(purchase))

		notification = Notification.objects.take(
			updater  = self.updater,
			code     = self.get_int(element, './id'),
			url      = self.get_text(element, './printForm/url'),
			purchase = purchase)

		for a in element.xpath('.//attachments/attachment'):

			attachment = Attachment.objects.take(
				url         = self.get_text(a, './url'),
				name        = self.get_text(a, './fileName'),
				size        = self.get_text(a, './fileSize'),
				description = self.get_text(a, './docDescription'))

			link = PurchaseToAttachment.objects.write(
				purchase   = purchase,
				attachment = attachment,
				doc_type   = None)

		for n, l in enumerate(element.xpath('.//lot')):

			currency = Currency.objects.take(code = self.get_text(l, './currency/code'))


		# TODO ??
			#plan_number     = self.get_text(l, './customerRequirements/tenderPlanInfo/planNumber')
			#position_number = self.get_text(l, './customerRequirements/tenderPlanInfo/positionNumber')

			if self.get_int(l, './lotNumber'):
				number = self.get_int(l, './lotNumber')
			else:
				number = n

			lot = Lot.objects.write(
				purchase       = purchase,
				number         = number,
				name           = self.get_text(l, './lotObjectInfo'),
				finance_source = self.get_text(l, './financeSource'),
				max_price      = self.get_float(l, './maxPrice'))

			if lot:

				lot.products.clear()
				for p in l.xpath('./purchaseObjects/purchaseObject'):

					try:
						okpd = OKPD.objects.get(code = self.get_text(p, './OKPD/code'))
					except Exception:
						okpd = None

					try:
						okpd2 = OKPD2.objects.get(code = self.get_text(p, './OKPD2/code'))
					except Exception:
						okpd2 = None

					product = Product.objects.take(
						okpd  = okpd,
						okpd2 = okpd2,
						name  = self.get_text(p, './name'))

					okei = OKEI.objects.take(
						code = self.get_text(p, './OKEI/code'))

					link = LotToProduct()
					link.lot      = lot
					link.product  = product
					link.quantity = self.get_float(p, './quantity')
					link.okei     = okei
					link.price    = self.get_float(p, './price')
					link.total    = self.get_float(p, './sum')
					link.currency = currency
					link.save()

				lot.customers.clear()
				for c in l.xpath('./customerRequirements/customerRequirement/customer'):

					customer = OrganisationExtKey.objects.get_organisation(
						updater = self.updater,
						ext_key = self.get_text(c, './regNum'))

					link = LotToCustomer()
					link.lot      = lot
					link.customer = customer
					link.save()

		return True



	def parse_notification_tender_prolongation(self, element, region):

		purchase = Purchase.objects.take(number = self.get_text(element, './purchaseNumber'), region = region)

		doc_type = self.get_text(element, './docType/code')

		if doc_type == 'IPP':
			purchase.collecting_end_time    = self.get_datetime(element, './collectingProlongationDate')
			purchase.save()
		elif doc_type == 'UP':
			purchase.scoring_time    = self.get_datetime(element, './scoringProlongationDate')
			purchase.save()
		else:
			return False

		print('{} - prolongated'.format(purchase))

		notification = Notification.objects.take(
			updater  = self.updater,
			code     = self.get_int(element, './id'),
			url      = self.get_text(element, './printForm/url'),
			purchase = purchase)

		return True



	def parse_notification_tender_cancel(self, element, region):

		purchase = Purchase.objects.take(number = self.get_text(element, './purchaseNumber'), region = region)

		notification = Notification.objects.take(
			updater  = self.updater,
			code     = self.get_int(element, './id'),
			url      = self.get_text(element, './printForm/url'),
			purchase = purchase)

		purchase.cancel()

		print('{} - canceled'.format(purchase))

		return True



	def parse_notification_lot_change(self, element, region):

		responsible = OrganisationExtKey.objects.get_organisation(
			updater = self.updater,
			ext_key = self.get_text(element, './purchaseResponsible/responsibleOrg/regNum'))

		specialised = OrganisationExtKey.objects.get_organisation(
			updater = self.updater,
			ext_key = self.get_text(element, './purchaseResponsible/specializedOrg/regNum'))

		# TODO TEST
		import xml.etree.ElementTree as ET
		if not responsible:
			print(ET.tostring(element, encoding = 'unicode'))
			print('Ответственного нет!!!')

		email = Email.objects.take(email = self.get_text(element, './purchaseResponsible/responsibleInfo/contactEMail'))
		phone = Phone.objects.take(phone = self.get_text(element, './purchaseResponsible/responsibleInfo/contactPhone'))

		contact_person = Person.objects.take(
			first_name  = self.get_text(element, './purchaseResponsible/responsibleInfo/contactPerson/firstName'),
			middle_name = self.get_text(element, './purchaseResponsible/responsibleInfo/contactPerson/middleName'),
			last_name   = self.get_text(element, './purchaseResponsible/responsibleInfo/contactPerson/lastName'),
			email       = email,
			phon        = phone)

		placing_way = PlacingWay.objects.take(code = self.get_text(element, './placingWay/code'))

		grant_place            = Address.objects.take(address = self.get_text(element, './purchaseDocumentation/grantPlace'))
		collecting_place       = Address.objects.take(address = self.get_text(element, './procedureInfo/collecting/place'))
		opening_place          = Address.objects.take(address = self.get_text(element, './procedureInfo/opening/place'))
		prequalification_place = Address.objects.take(address = self.get_text(element, './procedureInfo/prequalification/place'))
		scoring_place          = Address.objects.take(address = self.get_text(element, './procedureInfo/scoring/place'))

		etp = ETP.objects.take(
			code = self.get_text(element, './ETP/code'),
			name = self.get_text(element, './ETP/name'),
			url  = self.get_text(element, './ETP/url'))

		ok = False

		for info in element.xpath('//procedureOKInfo'):

			collecting_start_time  = self.get_datetime(info, './procedureInfo/collecting/startDate'),
			collecting_end_time    = self.get_datetime(info, './procedureInfo/collecting/endDate'),
			opening_time           = self.get_datetime(info, './procedureInfo/opening/date'),
			scoring_time           = self.get_datetime(info, './procedureInfo/scoring/date'),
			ok = True

		if not ok:
			return False

		purchase = Purchase.objects.write(
			number                 = self.get_text(element, './purchaseNumber'),
			name                   = self.get_text(element, './purchaseObjectInfo'),
			url                    = self.get_text(element, './href'),
			published              = self.get_datetime(element, './docPublishDate'),
			region                 = region,
			responsible            = responsible,
			specialised            = specialised,
			contact_person         = contact_person,
			placing_way            = placing_way,

			grant_place            = Address.objects.take(address = self.get_text(element, './purchaseDocumentation/grantPlace')),
			collecting_place       = Address.objects.take(address = self.get_text(element, './procedureInfo/collecting/place')),
			opening_place          = Address.objects.take(address = self.get_text(element, './procedureInfo/opening/place')),
			final_opening_place    = Address.objects.take(address = self.get_text(element, './procedureInfo/finalOpening/place')),
			prequalification_place = Address.objects.take(address = self.get_text(element, './procedureInfo/prequalification/place')),
			selecting_place        = Address.objects.take(address = self.get_text(element, './procedureInfo/selecting/place')),
			scoring_place          = Address.objects.take(address = self.get_text(element, './procedureInfo/scoring/place')),

			collecting_st1_place   = Address.objects.take(address = self.get_text(element, './procedureInfo/stageOne/collecting/place')),
			opening_st1_place      = Address.objects.take(address = self.get_text(element, './procedureInfo/stageOne/opening/place')),
			scoring_st1_place      = Address.objects.take(address = self.get_text(element, './procedureInfo/stageOne/scoring/place')),

			collecting_st2_place   = Address.objects.take(address = self.get_text(element, './procedureInfo/stageTwo/collecting/place')),
			opening_st2_place      = Address.objects.take(address = self.get_text(element, './procedureInfo/stageTwo/opening/place')),
			scoring_st2_place      = Address.objects.take(address = self.get_text(element, './procedureInfo/stageTwo/scoring/place')),

			etp                    = etp,

			grant_start_time       = self.get_datetime(element, './purchaseDocumentation/grantStartDate'),
			grant_end_time         = self.get_datetime(element, './purchaseDocumentation/grantEndDate'),

			collecting_start_time  = self.get_datetime(element, './procedureInfo/collecting/startDate'),
			collecting_end_time    = self.get_datetime(element, './procedureInfo/collecting/endDate'),
			opening_time           = self.get_datetime(element, './procedureInfo/opening/date'),
			final_opening_time     = self.get_datetime(element, './procedureInfo/finalOpening/date'),
			prequalification_time  = self.get_datetime(element, './procedureInfo/prequalification/date'),
			selecting_time         = self.get_datetime(element, './procedureInfo/selecting/date'),
			scoring_time           = self.get_datetime(element, './procedureInfo/scoring/date'),
			bidding_time           = self.get_datetime(element, './procedureInfo/bidding/date'),

			collecting_st1_start_time  = self.get_datetime(element, './procedureInfo/stageOne/collecting/startDate'),
			collecting_st1_end_time    = self.get_datetime(element, './procedureInfo/stageOne/collecting/endDate'),
			opening_st1_time           = self.get_datetime(element, './procedureInfo/stageOne/opening/date'),
			scoring_st1_time           = self.get_datetime(element, './procedureInfo/stageOne/scoring/date'),
			collecting_st2_start_time  = self.get_datetime(element, './procedureInfo/stageTwo/collecting/startDate'),
			collecting_st2_end_time    = self.get_datetime(element, './procedureInfo/stageTwo/collecting/endDate'),
			opening_st2_time           = self.get_datetime(element, './procedureInfo/stageTwo/opening/date'),
			scoring_st2_time           = self.get_datetime(element, './procedureInfo/stageTwo/scoring/date'))

		print('{} - edited'.format(purchase))

		notification = Notification.objects.take(
			updater  = self.updater,
			code     = self.get_int(element, './id'),
			url      = self.get_text(element, './printForm/url'),
			purchase = purchase)

		for a in element.xpath('.//attachments/attachment'):

			attachment = Attachment.objects.take(
				url         = self.get_text(a, './url'),
				name        = self.get_text(a, './fileName'),
				size        = self.get_text(a, './fileSize'),
				description = self.get_text(a, './docDescription'))

			link = PurchaseToAttachment.objects.write(
				purchase   = purchase,
				attachment = attachment,
				doc_type   = None)


		for n, l in enumerate(element.xpath('.//lot')):

			currency = Currency.objects.take(code = self.get_text(l, './currency/code'))


		# TODO ??
			#plan_number     = self.get_text(l, './customerRequirements/tenderPlanInfo/planNumber')
			#position_number = self.get_text(l, './customerRequirements/tenderPlanInfo/positionNumber')
			if self.get_int(l, './lotNumber'):
				number = self.get_int(l, './lotNumber')
			else:
				number = n

			lot = Lot.objects.write(
				purchase       = purchase,
				number         = number,
				name           = self.get_text(l, './lotObjectInfo'),
				finance_source = self.get_text(l, './financeSource'),
				max_price      = self.get_float(l, './maxPrice'))

			if lot:

				lot.products.clear()
				for p in l.xpath('./purchaseObjects/purchaseObject'):

					try:
						okpd = OKPD.objects.get(code = self.get_text(p, './OKPD/code'))
					except Exception:
						okpd = None

					try:
						okpd2 = OKPD2.objects.get(code = self.get_text(p, './OKPD2/code'))
					except Exception:
						okpd2 = None

					product = Product.objects.take(
						okpd  = okpd,
						okpd2 = okpd2,
						name  = self.get_text(p, './name'))

					okei = OKEI.objects.take(
						code = self.get_text(p, './OKEI/code'))

					link = LotToProduct()
					link.lot      = lot
					link.product  = product
					link.quantity = self.get_float(p, './quantity')
					link.okei     = okei
					link.price    = self.get_float(p, './price')
					link.total    = self.get_float(p, './sum')
					link.currency = currency
					link.save()

				lot.customers.clear()
				for c in l.xpath('./customerRequirements/customerRequirement/customer'):

					customer = OrganisationExtKey.objects.get_organisation(
						updater = self.updater,
						ext_key = self.get_text(c, './regNum'))

					link = LotToCustomer()
					link.lot      = lot
					link.customer = customer
					link.save()

		return True



	def parse_notification_lot_cancel(self, element, region):

		purchase = Purchase.objects.take(number = self.get_text(element, './purchaseNumber'), region = region)

		notification = Notification.objects.take(
			updater  = self.updater,
			code     = self.get_int(element, './id'),
			url      = self.get_text(element, './printForm/url'),
			purchase = purchase)

		lot = Lot.objects.take(
				purchase = purchase,
				number   = self.get_text(element, './lot/lotNumber')
			)

		lot.cancel()

		print('{} - lot {} canceled'.format(purchase, lot.number))

		return True



	def parse_notification_sign(self, element, region):

		purchase = Purchase.objects.take(
			number = self.get_text(element, './foundation/order/purchaseNumber'),
			region = region)
		print('{} - contract sign'.format(purchase))

		customer = OrganisationExtKey.objects.get_organisation(
			updater = self.updater,
			ext_key = self.get_text(element, './customer/regNum'))

		currency = Currency.objects.take(code = self.get_text(element, './currency/code'))

		contract = Contract.objects.take(
			purchase   = purchase,
			customer   = customer,
			currency   = currency,
			number     = self.get_text(element, './number'),
			price      = self.get_float(element, './price'),
			price_rub  = self.get_float(element, './priceRUR'),
			sign_date  = self.get_text(element, './signDate'))

		contract.suppliers.clear()
		for s in element.xpath('.//supplier'):

			supplier = Organisation.objects.take(
				inn = self.get_text(s, './inn'),
				kpp = self.get_text(s, './kpp'),
				full_name = self.get_text(s, './organizationName'))

			contact = Person.objects.take(
				first_name  = self.get_text(s, './contactInfo/firstName'),
				middle_name = self.get_text(s, './contactInfo/middleName'),
				last_name   = self.get_text(s, './contactInfo/lastName'))

			link = ContractToSupplier.objects.take(
				contract = contract,
				supplier = supplier,
				contact  = contact)

		return True


	def parse_notification_document(self, element, region):

		purchase = Purchase.objects.take(number = self.get_text(element, './purchaseNumber'), region = region)
		print('{} - document added'.format(purchase))

		doc_type = DocType.objects.take(
			code = self.get_text(element, './docType/code'),
			name = self.get_text(element, './docType/name'))

		doc_type.code = self.get_text(element, './docType/code')

		if doc_type.code == 'RD': # Разъяснения положений документации об электронном аукционе

			for a in element.xpath('.//attachments/attachment'):

				attachment = Attachment.objects.take(
					url         = self.get_text(a, './url'),
					name        = self.get_text(a, './fileName'),
					size        = self.get_text(a, './fileSize'),
					description = self.get_text(a, './docDescription'))

				link = PurchaseToAttachment.objects.write(
					purchase   = purchase,
					attachment = attachment,
					doc_type   = doc_type)

		else:
			return False

		notification = Notification.objects.take(
			updater  = self.updater,
			code     = self.get_int(element, './id'),
			url      = self.get_text(element, './printForm/url'),
			purchase = purchase)

		return True



	def parse_notification_protocol(self, element, region):

		purchase = Purchase.objects.take(number = self.get_text(element, './purchaseNumber'), region = region)
		print('{} - protocol added'.format(purchase))











		return False




	def get_text(self, element, query):

		try:
			result = element.xpath(query)[0].text.strip()
		except Exception:
			result = ''

		return result


	def get_bool(self, element, query):

		try:
			if element.xpath(query)[0].text == 'true':
				result = True
			else:
				result = False
		except Exception:
			result = False

		return result


	def get_datetime(self, element, query):

		try:
			result = element.xpath(query)[0].text.strip()
		except Exception:
			result = None

		return result


	def get_int(self, element, query):

		try:
			result = int(element.xpath(query)[0].text.strip())
		except Exception:
			result = None

		return result


	def get_float(self, element, query):

		try:
			result = float(element.xpath(query)[0].text.strip())
		except Exception:
			result = None

		return result

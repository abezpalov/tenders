import datetime

import tenders.runner
from tenders.models import *


class Runner(tenders.runner.Runner):


	name  = 'Zakupki.gov.ru FZ223'
	alias = 'fz223'

	black_list = ['archive', 'undefined']

	categories = {
		'essences' : 'out/nsi',
		'regions'  : 'out/published'}

	subcategories = [
		None,
		'daily'
		]


	def __init__(self):

		super().__init__()

		self.max_time = datetime.timedelta(0, 60*60*23, 0)

		self.url = 'ftp.zakupki.gov.ru'

		self.essences = [
			{'category' : 'nsiOkdp',           'parser' : self.parse_okdp},
			{'category' : 'nsiOkato',          'parser' : self.parse_okato},
			{'category' : 'nsiOkei',           'parser' : self.parse_okei},


#			{'category' : 'nsiAgency',         'parser' : self.parse_agency},
#			{'category' : 'nsiClauseType',     'parser' : self.parse_},
#			{'category' : 'nsiOkfs',           'parser' : self.parse_},
#			{'category' : 'nsiOkogu',          'parser' : self.parse_},
#			{'category' : 'nsiOkopf',          'parser' : self.parse_},
#			{'category' : 'nsiOkpd2',          'parser' : self.parse_},
#			{'category' : 'nsiOktmo',          'parser' : self.parse_},
#			{'category' : 'nsiOkv',            'parser' : self.parse_},
#			{'category' : 'nsiOkved',          'parser' : self.parse_},
#			{'category' : 'nsiOkved2',         'parser' : self.parse_},
#			{'category' : 'nsiOrganisation',   'parser' : self.parse_},
#			{'category' : 'nsiProtokol',       'parser' : self.parse_},
#			{'category' : 'nsiPurchaseMethod', 'parser' : self.parse_},
		]

		self.region_essences = [
#			{'category' : 'plangraphs',    'parser' : self.parse_plan},
#			{'category' : 'notifications', 'parser' : self.parse_notification},
		]


	def run(self):


		if not self.updater.login or not self.updater.password:
			print('Ошибка: Проверьте параметры авторизации. Кажется их нет.')
			return False

		# Обновляем справочники
		for essence in self.essences:

			# Проверяем не вышло ли время
			if self.is_time_up():
				return True

			self.update_essence(essence)


		print('Обновляем данные с регионов')

		for essence in self.region_essences:

			for region_key in self.get_ftp_catalog(self.url, self.categories['regions']):

				if (not region_key in self.black_list) and (not '.'in region_key):
					try:
						self.get_ftp_catalog(self.url, '{}/{}'.format(self.categories['regions'], region))
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

		for subcategory in self.subcategories:

			if subcategory:
				catalog = "{}/{}/{}".format(self.categories['essences'], essence['category'], subcategory)
			else:
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


	def parse_okdp(self, tree):
		'Парсит ОКДП.'

		# TODO KILL
		import xml.etree.ElementTree as ET
#		print(ET.tostring(element, encoding = 'unicode'))


		for element in tree.xpath('.//item'):

			parent = OKDP.objects.take(code = self.get_text(element, './nsiOkdpData/parentCode'))

			okdp = OKDP.objects.write(
				code = self.get_text(element, './nsiOkdpData/code'),
				name = self.get_text(element, './nsiOkdpData/name'),
				parent        = parent,
				state         = True)
			print("ОКДП: {}.".format(okdp))

		return True


	def parse_okato(self, tree):
		'Парсит ОКАТО (классификация населённых пунктов'

		for element in tree.xpath('.//item'):

			parent = OKATO.objects.take(code = self.get_text(element, './nsiOkatoData/parentCode'))

			okato = OKATO.objects.write(
				code = self.get_text(element, './nsiOkatoData/code'),
				name = self.get_text(element, './nsiOkatoData/name'),
				parent        = parent,
				state         = True)
			print("ОКАТО: {}.".format(okato))

		return True


	def parse_okei(self, tree):
		'Парсит ОКЕИ (единицы измерения)'

		for element in tree.xpath('.//item'):

			section = OKEISection.objects.take(
				code  = self.get_text(element, './nsiOkeiData/section/code'),
				name  = self.get_text(element, './nsiOkeiData/section/name'),
				state = True)

			group = OKEIGroup.objects.take(
				code  = self.get_text(element, './nsiOkeiData/group/code'),
				name  = self.get_text(element, './nsiOkeiData/group/name'),
				state = True)

			okei = OKEI.objects.write(
				code    = self.get_text(element, './nsiOkeiData/code'),
				section = section,
				group   = group,
				name    = self.get_text(element, './nsiOkeiData/name'),
				symbol  = self.get_text(element, './nsiOkeiData/symbol'))
			print("Единица измерения: {}.".format(okei))

		return True


	def parse_organisation(self, tree):

		for element in tree.xpath('.//nsiOrganizationData'):

			legal_address   = Address.objects.take(address = self.get_text(element, './mainInfo/legalAddress'))
			postal_address  = Address.objects.take(address = self.get_text(element, './mainInfo/postalAddress'))

			email = Email.objects.take(email = self.get_text(element, './contactInfo/email'))
			phone = Phone.objects.take(phone = self.get_text(element, './contactInfo/phone'))
			website = URL.objects.take(url = self.get_text(element, './contactInfo/website'))





			contact_person = Person.objects.take(
				first_name  = self.get_text(element, './contactPerson/firstName'),
				middle_name = self.get_text(element, './contactPerson/middleName'),
				last_name   = self.get_text(element, './contactPerson/lastName'),
				email       = email,
				phone       = phone,
				website     = website)

			ext_key = OrganisationExtKey.objects.take(
				updater = self.updater,
				ext_key = self.get_text(element, './headAgency/regNum'))
			if ext_key:
				head_agency = ext_key.organisation
			else:
				head_agency = None

			ext_key = OrganisationExtKey.objects.take(
				updater = self.updater,
				ext_key = self.get_text(element, './orderingAgency/regNum'))
			if ext_key:
				ordering_agency = ext_key.organisation
			else:
				ordering_agency = None

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
				website           = website,
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

			ext_key = OrganisationExtKey.objects.write(
				updater = self.updater,
				ext_key = self.get_text(element, './regNumber'),
				organisation = organisation)
			print('Организация: {}'.format(organisation))









# TODO END
















	def clear_tags(self, tree):

		# Чистим теги
		for element in tree.xpath('.//*'):
			element.tag = element.tag.split('}')[1]

		return tree



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

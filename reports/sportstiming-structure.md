# Sportstiming structure discovery

Public `/app/results` views are reachable without the human-verification page. This report stores form/select/link structure, not a raw HTML mirror.

## 2018 (event 4950)

- HTML sampled: 87404 bytes
- Forms: 0
- Selects: 3
- Relevant links: 58

- Select 1 attrs `{'name': None, 'class': 'form-control selectDistance'}`: 15266=Simris Alg Ultra 60km+ (ca. 1150m höjdmeter); 15268=Verkeån trail 21km+ (ca. 500m höjdmeter); 15265=Naturloppet 5km+; 15269=Ekopark trail 13 km
- Select 2 attrs `{'name': None, 'class': 'form-control selectGender'}`: A=Män/Kvinnor; M=Män; F=Kvinnor
- Select 3 attrs `{'name': None, 'class': 'form-control selectCountry'}`: all=Alla länder; 14=Belgien; 37=Danmark; 52=Finland; 53=Frankrig; 77=Italien; 128=Norge; 198=Storbritannien; 161=Sverige; 999=Ukendt land; 185=USA

Link patterns:
- `/event/4950/app/results/{result_id}` × 50
- `/event/4950/app/results?page={page}` × 4
- `/event/4950/app` × 1
- `/event/4950/app/participants` × 1
- `/event/4950/app/results` × 1
- `/event/4950/app/tracking` × 1

Candidate endpoint strings:
- `#athletesearchpanel`
- `);$.ajax({url: `
- `);if (searchFields.length > 0)searchFields[0].focus();}, 0);});});function setSelect2(nodeSet) {nodeSet.select2({ dropdownAutoWidth: true, width: `
- `, function (e) {window.setTimeout(function () {var searchFields = $(`
- `/js/resultlist.js?2.0`
- `ResultListDoSearch(`
- `athletesearchpanel`
- `btn btn-primary float-end btnSearch`
- `btnSearch`
- `expandsearch_label`

## 2019 (event 5719)

- HTML sampled: 89465 bytes
- Forms: 0
- Selects: 3
- Relevant links: 59

- Select 1 attrs `{'name': None, 'class': 'form-control selectDistance'}`: 20385=Simris Alg Ultra 60km+ (ca. 1450m höjdmeter); 20387=Verkeån trail 21km+; 20390=Duo Trail (relay 2 x 30 km); 20384=Naturloppet 5km+; 20388=Ekopark trail 13 km
- Select 2 attrs `{'name': None, 'class': 'form-control selectGender'}`: A=Män/Kvinnor; M=Män; F=Kvinnor
- Select 3 attrs `{'name': None, 'class': 'form-control selectCountry'}`: all=Alla länder; 37=Danmark; 45=England; 52=Finland; 53=Frankrig; 74=Irland; 102=Malaysia; 128=Norge; 147=Schweiz; 157=Spanien; 198=Storbritannien; 161=Sverige; 164=Sydkorea; 179=Tyskland; 999=Ukendt land

Link patterns:
- `/event/5719/app/results/{result_id}` × 50
- `/event/5719/app/results?page={page}` × 4
- `/event/5719/app` × 1
- `/event/5719/app/participants` × 1
- `/event/5719/app/points` × 1
- `/event/5719/app/results` × 1
- `/event/5719/app/tracking` × 1

Candidate endpoint strings:
- `#athletesearchpanel`
- `);$.ajax({url: `
- `);if (searchFields.length > 0)searchFields[0].focus();}, 0);});});function setSelect2(nodeSet) {nodeSet.select2({ dropdownAutoWidth: true, width: `
- `, function (e) {window.setTimeout(function () {var searchFields = $(`
- `/js/resultlist.js?2.0`
- `ResultListDoSearch(`
- `athletesearchpanel`
- `btn btn-primary float-end btnSearch`
- `btnSearch`
- `expandsearch_label`

## 2022 (event 9587)

- HTML sampled: 102708 bytes
- Forms: 0
- Selects: 11
- Relevant links: 57

- Select 1 attrs `{'name': None, 'class': 'form-control selectDistance'}`: 46204=Ultra 60km+; 46206=Teleservice trail 21km+; 46209=Duo Trail (relay 2 x 30 km); 46207=Ekopark trail 13 km; 46203=Naturloppet 5km+
- Select 2 attrs `{'name': None, 'class': 'form-control selectGender'}`: A=Män/Kvinnor; M=Män; F=Kvinnor
- Select 3 attrs `{'name': None, 'class': ' form-control selectCategory selectCategory_46204', 'style': 'display:none;'}`: all=Alla; 27580=0-11 år; 27581=12-13 år; 27582=14-15 år; 27583=16-17 år; 27584=18-19 år; 27585=20-24 år; 27586=25-29 år; 27587=30-34 år; 27588=35-39 år; 27589=40-44 år; 27590=45-49 år; 27591=50-54 år; 27592=55-59 år; 27593=60-64 år; 27594=65-69 år; 27595=70-74 år; 27596=75-79 år; 27597=80-84 år; 27598=85-89 år; 27599=90+ år; 27600=championship för Joelette
- Select 4 attrs `{'name': None, 'class': ' form-control selectCategory selectCategory_46206', 'style': 'display:none;'}`: all=Alla; 27580=0-11 år; 27581=12-13 år; 27582=14-15 år; 27583=16-17 år; 27584=18-19 år; 27585=20-24 år; 27586=25-29 år; 27587=30-34 år; 27588=35-39 år; 27589=40-44 år; 27590=45-49 år; 27591=50-54 år; 27592=55-59 år; 27593=60-64 år; 27594=65-69 år; 27595=70-74 år; 27596=75-79 år; 27597=80-84 år; 27598=85-89 år; 27599=90+ år; 27600=championship för Joelette
- Select 5 attrs `{'name': None, 'class': ' form-control selectCategory selectCategory_46209', 'style': 'display:none;'}`: all=Alla; 27580=0-11 år; 27581=12-13 år; 27582=14-15 år; 27583=16-17 år; 27584=18-19 år; 27585=20-24 år; 27586=25-29 år; 27587=30-34 år; 27588=35-39 år; 27589=40-44 år; 27590=45-49 år; 27591=50-54 år; 27592=55-59 år; 27593=60-64 år; 27594=65-69 år; 27595=70-74 år; 27596=75-79 år; 27597=80-84 år; 27598=85-89 år; 27599=90+ år; 27600=championship för Joelette
- Select 6 attrs `{'name': None, 'class': ' form-control selectCategory selectCategory_46207'}`: all=Alla; 27580=0-11 år; 27581=12-13 år; 27582=14-15 år; 27583=16-17 år; 27584=18-19 år; 27585=20-24 år; 27586=25-29 år; 27587=30-34 år; 27588=35-39 år; 27589=40-44 år; 27590=45-49 år; 27591=50-54 år; 27592=55-59 år; 27593=60-64 år; 27594=65-69 år; 27595=70-74 år; 27596=75-79 år; 27597=80-84 år; 27598=85-89 år; 27599=90+ år; 27600=championship för Joelette
- Select 7 attrs `{'name': None, 'class': ' form-control selectCategory selectCategory_46203', 'style': 'display:none;'}`: all=Alla; 27580=0-11 år; 27581=12-13 år; 27582=14-15 år; 27583=16-17 år; 27584=18-19 år; 27585=20-24 år; 27586=25-29 år; 27587=30-34 år; 27588=35-39 år; 27589=40-44 år; 27590=45-49 år; 27591=50-54 år; 27592=55-59 år; 27593=60-64 år; 27594=65-69 år; 27595=70-74 år; 27596=75-79 år; 27597=80-84 år; 27598=85-89 år; 27599=90+ år; 27600=championship för Joelette
- Select 8 attrs `{'name': None, 'class': ' form-control selectCategory selectCategory_46208', 'style': 'display:none;'}`: all=Alla; 27580=0-11 år; 27581=12-13 år; 27582=14-15 år; 27583=16-17 år; 27584=18-19 år; 27585=20-24 år; 27586=25-29 år; 27587=30-34 år; 27588=35-39 år; 27589=40-44 år; 27590=45-49 år; 27591=50-54 år; 27592=55-59 år; 27593=60-64 år; 27594=65-69 år; 27595=70-74 år; 27596=75-79 år; 27597=80-84 år; 27598=85-89 år; 27599=90+ år; 27600=championship för Joelette
- Select 9 attrs `{'name': None, 'class': ' form-control selectCategory selectCategory_46205', 'style': 'display:none;'}`: all=Alla; 27580=0-11 år; 27581=12-13 år; 27582=14-15 år; 27583=16-17 år; 27584=18-19 år; 27585=20-24 år; 27586=25-29 år; 27587=30-34 år; 27588=35-39 år; 27589=40-44 år; 27590=45-49 år; 27591=50-54 år; 27592=55-59 år; 27593=60-64 år; 27594=65-69 år; 27595=70-74 år; 27596=75-79 år; 27597=80-84 år; 27598=85-89 år; 27599=90+ år; 27600=championship för Joelette
- Select 10 attrs `{'name': None, 'class': ' form-control selectCategory selectCategory_52720', 'style': 'display:none;'}`: all=Alla; 27580=0-11 år; 27581=12-13 år; 27582=14-15 år; 27583=16-17 år; 27584=18-19 år; 27585=20-24 år; 27586=25-29 år; 27587=30-34 år; 27588=35-39 år; 27589=40-44 år; 27590=45-49 år; 27591=50-54 år; 27592=55-59 år; 27593=60-64 år; 27594=65-69 år; 27595=70-74 år; 27596=75-79 år; 27597=80-84 år; 27598=85-89 år; 27599=90+ år; 27600=championship för Joelette
- Select 11 attrs `{'name': None, 'class': 'form-control selectCountry'}`: all=Alla länder; 9=Australien; 14=Belgien; 37=Danmark; 52=Finland; 53=Frankrig; 60=Grækenland; 67=Holland; 74=Irland; 75=Island; 84=Kina; 92=Letland; 97=Litauen; 128=Norge; 137=Polen; 157=Spanien; 198=Storbritannien; 161=Sverige; 179=Tyskland; 999=Ukendt land; 182=Ukraine

Link patterns:
- `/event/9587/app/results/{result_id}` × 50
- `/event/9587/app/results?page={page}` × 3
- `/event/9587/app` × 1
- `/event/9587/app/participants` × 1
- `/event/9587/app/results` × 1
- `/event/9587/app/tracking` × 1

Candidate endpoint strings:
- `#athletesearchpanel`
- `);$.ajax({url: `
- `);if (searchFields.length > 0)searchFields[0].focus();}, 0);});});function setSelect2(nodeSet) {nodeSet.select2({ dropdownAutoWidth: true, width: `
- `, function (e) {window.setTimeout(function () {var searchFields = $(`
- `/js/resultlist.js?2.0`
- `ResultListDoSearch(`
- `athletesearchpanel`
- `btn btn-primary float-end btnSearch`
- `btnSearch`
- `expandsearch_label`

## 2023 (event 11274)

- HTML sampled: 97203 bytes
- Forms: 0
- Selects: 12
- Relevant links: 57

- Select 1 attrs `{'name': None, 'class': 'form-control selectDistance'}`: 58343=Ultra 60km+; 58345=Fogarolli trail 21km+; 58348=Duo Trail (relay 2 x 30 km); 58346=Ekopark trail 13 km; 58342=Naturloppet 5km+
- Select 2 attrs `{'name': None, 'class': 'form-control selectGender'}`: A=Män/Kvinnor; M=Män; F=Kvinnor
- Select 3 attrs `{'name': None, 'class': ' form-control selectCategory selectCategory_58343', 'style': 'display:none;'}`: all=Alla; 30121=championship för Joelette; 30120=90+ år; 30119=85-89 år; 30118=80-84 år; 30117=75-79 år; 30116=70-74 år; 30115=65-69 år; 30114=60-64 år; 30113=55-59 år; 30112=50-54 år; 30111=45-49 år; 30110=40-44 år; 30109=35-39 år; 30108=30-34 år; 30107=25-29 år; 30106=20-24 år; 30105=18-19 år; 30104=16-17 år; 30103=14-15 år; 30102=12-13 år; 30101=0-11 år
- Select 4 attrs `{'name': None, 'class': ' form-control selectCategory selectCategory_58345', 'style': 'display:none;'}`: all=Alla; 30121=championship för Joelette; 30120=90+ år; 30119=85-89 år; 30118=80-84 år; 30117=75-79 år; 30116=70-74 år; 30115=65-69 år; 30114=60-64 år; 30113=55-59 år; 30112=50-54 år; 30111=45-49 år; 30110=40-44 år; 30109=35-39 år; 30108=30-34 år; 30107=25-29 år; 30106=20-24 år; 30105=18-19 år; 30104=16-17 år; 30103=14-15 år; 30102=12-13 år; 30101=0-11 år
- Select 5 attrs `{'name': None, 'class': ' form-control selectCategory selectCategory_58348', 'style': 'display:none;'}`: all=Alla; 30121=championship för Joelette; 30120=90+ år; 30119=85-89 år; 30118=80-84 år; 30117=75-79 år; 30116=70-74 år; 30115=65-69 år; 30114=60-64 år; 30113=55-59 år; 30112=50-54 år; 30111=45-49 år; 30110=40-44 år; 30109=35-39 år; 30108=30-34 år; 30107=25-29 år; 30106=20-24 år; 30105=18-19 år; 30104=16-17 år; 30103=14-15 år; 30102=12-13 år; 30101=0-11 år
- Select 6 attrs `{'name': None, 'class': ' form-control selectCategory selectCategory_58346'}`: all=Alla; 30121=championship för Joelette; 30120=90+ år; 30119=85-89 år; 30118=80-84 år; 30117=75-79 år; 30116=70-74 år; 30115=65-69 år; 30114=60-64 år; 30113=55-59 år; 30112=50-54 år; 30111=45-49 år; 30110=40-44 år; 30109=35-39 år; 30108=30-34 år; 30107=25-29 år; 30106=20-24 år; 30105=18-19 år; 30104=16-17 år; 30103=14-15 år; 30102=12-13 år; 30101=0-11 år
- Select 7 attrs `{'name': None, 'class': ' form-control selectCategory selectCategory_58342', 'style': 'display:none;'}`: all=Alla; 30121=championship för Joelette; 30120=90+ år; 30119=85-89 år; 30118=80-84 år; 30117=75-79 år; 30116=70-74 år; 30115=65-69 år; 30114=60-64 år; 30113=55-59 år; 30112=50-54 år; 30111=45-49 år; 30110=40-44 år; 30109=35-39 år; 30108=30-34 år; 30107=25-29 år; 30106=20-24 år; 30105=18-19 år; 30104=16-17 år; 30103=14-15 år; 30102=12-13 år; 30101=0-11 år
- Select 8 attrs `{'name': None, 'class': ' form-control selectCategory selectCategory_59371', 'style': 'display:none;'}`: all=Alla; 30121=championship för Joelette; 30120=90+ år; 30119=85-89 år; 30118=80-84 år; 30117=75-79 år; 30116=70-74 år; 30115=65-69 år; 30114=60-64 år; 30113=55-59 år; 30112=50-54 år; 30111=45-49 år; 30110=40-44 år; 30109=35-39 år; 30108=30-34 år; 30107=25-29 år; 30106=20-24 år; 30105=18-19 år; 30104=16-17 år; 30103=14-15 år; 30102=12-13 år; 30101=0-11 år
- Select 9 attrs `{'name': None, 'class': ' form-control selectCategory selectCategory_58347', 'style': 'display:none;'}`: all=Alla; 30121=championship för Joelette; 30120=90+ år; 30119=85-89 år; 30118=80-84 år; 30117=75-79 år; 30116=70-74 år; 30115=65-69 år; 30114=60-64 år; 30113=55-59 år; 30112=50-54 år; 30111=45-49 år; 30110=40-44 år; 30109=35-39 år; 30108=30-34 år; 30107=25-29 år; 30106=20-24 år; 30105=18-19 år; 30104=16-17 år; 30103=14-15 år; 30102=12-13 år; 30101=0-11 år
- Select 10 attrs `{'name': None, 'class': ' form-control selectCategory selectCategory_58344', 'style': 'display:none;'}`: all=Alla; 30121=championship för Joelette; 30120=90+ år; 30119=85-89 år; 30118=80-84 år; 30117=75-79 år; 30116=70-74 år; 30115=65-69 år; 30114=60-64 år; 30113=55-59 år; 30112=50-54 år; 30111=45-49 år; 30110=40-44 år; 30109=35-39 år; 30108=30-34 år; 30107=25-29 år; 30106=20-24 år; 30105=18-19 år; 30104=16-17 år; 30103=14-15 år; 30102=12-13 år; 30101=0-11 år
- Select 11 attrs `{'name': None, 'class': ' form-control selectCategory selectCategory_58349', 'style': 'display:none;'}`: all=Alla; 30121=championship för Joelette; 30120=90+ år; 30119=85-89 år; 30118=80-84 år; 30117=75-79 år; 30116=70-74 år; 30115=65-69 år; 30114=60-64 år; 30113=55-59 år; 30112=50-54 år; 30111=45-49 år; 30110=40-44 år; 30109=35-39 år; 30108=30-34 år; 30107=25-29 år; 30106=20-24 år; 30105=18-19 år; 30104=16-17 år; 30103=14-15 år; 30102=12-13 år; 30101=0-11 år
- Select 12 attrs `{'name': None, 'class': 'form-control selectCountry'}`: all=Alla länder; 22=Brasilien; 37=Danmark; 52=Finland; 53=Frankrig; 67=Holland; 74=Irland; 75=Island; 77=Italien; 79=Japan; 106=Marokko; 128=Norge; 137=Polen; 147=Schweiz; 149=Serbien; 157=Spanien; 198=Storbritannien; 161=Sverige; 163=Sydafrika; 164=Sydkorea; 171=Tjekkiet; 179=Tyskland; 999=Ukendt land; 182=Ukraine; 185=USA

Link patterns:
- `/event/11274/app/results/{result_id}` × 50
- `/event/11274/app/results?page={page}` × 4
- `/event/11274/app` × 1
- `/event/11274/app/participants` × 1
- `/event/11274/app/results` × 1

Candidate endpoint strings:
- `#athletesearchpanel`
- `);$.ajax({url: `
- `);if (searchFields.length > 0)searchFields[0].focus();}, 0);});});function setSelect2(nodeSet) {nodeSet.select2({ dropdownAutoWidth: true, width: `
- `, function (e) {window.setTimeout(function () {var searchFields = $(`
- `/js/resultlist.js?2.0`
- `ResultListDoSearch(`
- `athletesearchpanel`
- `btn btn-primary float-end btnSearch`
- `btnSearch`
- `expandsearch_label`

## 2024 (event 12349)

- HTML sampled: 93729 bytes
- Forms: 0
- Selects: 8
- Relevant links: 57

- Select 1 attrs `{'name': None, 'class': 'form-control selectDistance'}`: 65781=60 k ÖST ultra med COROS; 65782=Fogarolli trail 21km+; 65784=Duo Trail (relay 2 x 30 km); 65783=Ekopark trail 14 km; 65780=Naturloppet 5km+
- Select 2 attrs `{'name': None, 'class': 'form-control selectGender'}`: A=Män/Kvinnor; M=Män; F=Kvinnor
- Select 3 attrs `{'name': None, 'class': ' form-control selectCategory selectCategory_65781', 'style': 'display:none;'}`: all=Alla; 32721=90-; 32722=85-89; 32723=80-84; 32724=75-79; 32725=70-74; 32726=65-69; 32727=60-64; 32728=55-59; 32729=50-54; 32730=45-49; 32731=40-44; 32732=35-39; 32733=30-34; 32734=25-29; 32735=20-24; 32736=18-19; 32737=16-17; 32738=14-15; 32739=12-13; 32740=0-11
- Select 4 attrs `{'name': None, 'class': ' form-control selectCategory selectCategory_65782', 'style': 'display:none;'}`: all=Alla; 32721=90-; 32722=85-89; 32723=80-84; 32724=75-79; 32725=70-74; 32726=65-69; 32727=60-64; 32728=55-59; 32729=50-54; 32730=45-49; 32731=40-44; 32732=35-39; 32733=30-34; 32734=25-29; 32735=20-24; 32736=18-19; 32737=16-17; 32738=14-15; 32739=12-13; 32740=0-11
- Select 5 attrs `{'name': None, 'class': ' form-control selectCategory selectCategory_65784', 'style': 'display:none;'}`: all=Alla; 32721=90-; 32722=85-89; 32723=80-84; 32724=75-79; 32725=70-74; 32726=65-69; 32727=60-64; 32728=55-59; 32729=50-54; 32730=45-49; 32731=40-44; 32732=35-39; 32733=30-34; 32734=25-29; 32735=20-24; 32736=18-19; 32737=16-17; 32738=14-15; 32739=12-13; 32740=0-11
- Select 6 attrs `{'name': None, 'class': ' form-control selectCategory selectCategory_65783'}`: all=Alla; 32721=90-; 32722=85-89; 32723=80-84; 32724=75-79; 32725=70-74; 32726=65-69; 32727=60-64; 32728=55-59; 32729=50-54; 32730=45-49; 32731=40-44; 32732=35-39; 32733=30-34; 32734=25-29; 32735=20-24; 32736=18-19; 32737=16-17; 32738=14-15; 32739=12-13; 32740=0-11
- Select 7 attrs `{'name': None, 'class': ' form-control selectCategory selectCategory_65780', 'style': 'display:none;'}`: all=Alla; 32721=90-; 32722=85-89; 32723=80-84; 32724=75-79; 32725=70-74; 32726=65-69; 32727=60-64; 32728=55-59; 32729=50-54; 32730=45-49; 32731=40-44; 32732=35-39; 32733=30-34; 32734=25-29; 32735=20-24; 32736=18-19; 32737=16-17; 32738=14-15; 32739=12-13; 32740=0-11
- Select 8 attrs `{'name': None, 'class': 'form-control selectCountry'}`: all=Alla länder; 6=Argentina; 14=Belgien; 24=Bulgarien; 29=Canada; 31=Colombia; 37=Danmark; 52=Finland; 53=Frankrig; 60=Grækenland; 67=Holland; 70=Indien; 74=Irland; 75=Island; 77=Italien; 110=Mexico; 128=Norge; 138=Portugal; 149=Serbien; 155=Slovenien; 157=Spanien; 161=Sverige; 163=Sydafrika; 168=Taiwan; 171=Tjekkiet; 179=Tyskland; 182=Ukraine; 185=USA

Link patterns:
- `/event/12349/app/results/{result_id}` × 50
- `/event/12349/app/results?page={page}` × 4
- `/event/12349/app` × 1
- `/event/12349/app/participants` × 1
- `/event/12349/app/results` × 1

Candidate endpoint strings:
- `#athletesearchpanel`
- `);$.ajax({url: `
- `);if (searchFields.length > 0)searchFields[0].focus();}, 0);});});function setSelect2(nodeSet) {nodeSet.select2({ dropdownAutoWidth: true, width: `
- `, function (e) {window.setTimeout(function () {var searchFields = $(`
- `/js/resultlist.js?2.0`
- `ResultListDoSearch(`
- `athletesearchpanel`
- `btn btn-primary float-end btnSearch`
- `btnSearch`
- `expandsearch_label`

## 2025 (event 15015)

- HTML sampled: 94083 bytes
- Forms: 0
- Selects: 8
- Relevant links: 57

- Select 1 attrs `{'name': None, 'class': 'form-control selectDistance'}`: 84440=CRAFT Ultra 60 k; 84441=Fogarolli trail 22 K; 84443=Duo Trail (relay 2 x 30 km); 84442=Ekopark trail 14 km; 84439=Naturloppet 5km+
- Select 2 attrs `{'name': None, 'class': 'form-control selectGender'}`: A=Män/Kvinnor; M=Män; F=Kvinnor
- Select 3 attrs `{'name': None, 'class': ' form-control selectCategory selectCategory_84440', 'style': 'display:none;'}`: all=Alla; 40442=90-; 40443=85-89; 40444=80-84; 40445=75-79; 40446=70-74; 40447=65-69; 40448=60-64; 40449=55-59; 40450=50-54; 40451=45-49; 40452=40-44; 40453=35-39; 40454=30-34; 40455=25-29; 40456=20-24; 40457=18-19; 40458=16-17; 40459=14-15; 40460=12-13; 40461=0-11
- Select 4 attrs `{'name': None, 'class': ' form-control selectCategory selectCategory_84441', 'style': 'display:none;'}`: all=Alla; 40442=90-; 40443=85-89; 40444=80-84; 40445=75-79; 40446=70-74; 40447=65-69; 40448=60-64; 40449=55-59; 40450=50-54; 40451=45-49; 40452=40-44; 40453=35-39; 40454=30-34; 40455=25-29; 40456=20-24; 40457=18-19; 40458=16-17; 40459=14-15; 40460=12-13; 40461=0-11
- Select 5 attrs `{'name': None, 'class': ' form-control selectCategory selectCategory_84443', 'style': 'display:none;'}`: all=Alla; 40442=90-; 40443=85-89; 40444=80-84; 40445=75-79; 40446=70-74; 40447=65-69; 40448=60-64; 40449=55-59; 40450=50-54; 40451=45-49; 40452=40-44; 40453=35-39; 40454=30-34; 40455=25-29; 40456=20-24; 40457=18-19; 40458=16-17; 40459=14-15; 40460=12-13; 40461=0-11
- Select 6 attrs `{'name': None, 'class': ' form-control selectCategory selectCategory_84442'}`: all=Alla; 40442=90-; 40443=85-89; 40444=80-84; 40445=75-79; 40446=70-74; 40447=65-69; 40448=60-64; 40449=55-59; 40450=50-54; 40451=45-49; 40452=40-44; 40453=35-39; 40454=30-34; 40455=25-29; 40456=20-24; 40457=18-19; 40458=16-17; 40459=14-15; 40460=12-13; 40461=0-11
- Select 7 attrs `{'name': None, 'class': ' form-control selectCategory selectCategory_84439', 'style': 'display:none;'}`: all=Alla; 40442=90-; 40443=85-89; 40444=80-84; 40445=75-79; 40446=70-74; 40447=65-69; 40448=60-64; 40449=55-59; 40450=50-54; 40451=45-49; 40452=40-44; 40453=35-39; 40454=30-34; 40455=25-29; 40456=20-24; 40457=18-19; 40458=16-17; 40459=14-15; 40460=12-13; 40461=0-11
- Select 8 attrs `{'name': None, 'class': 'form-control selectCountry'}`: all=Alla länder; 6=Argentina; 14=Belgien; 29=Canada; 37=Danmark; 45=England; 52=Finland; 53=Frankrig; 60=Grækenland; 67=Holland; 70=Indien; 72=Irak; 74=Irland; 77=Italien; 97=Litauen; 110=Mexico; 121=New Zealand; 128=Norge; 137=Polen; 149=Serbien; 152=Singapore; 155=Slovenien; 157=Spanien; 198=Storbritannien; 161=Sverige; 163=Sydafrika; 164=Sydkorea; 167=Tadsjikistan; 171=Tjekkiet; 179=Tyskland

Link patterns:
- `/event/15015/app/results/{result_id}` × 50
- `/event/15015/app/results?page={page}` × 4
- `/event/15015/app` × 1
- `/event/15015/app/participants` × 1
- `/event/15015/app/results` × 1

Candidate endpoint strings:
- `#athletesearchpanel`
- `);$.ajax({url: `
- `);if (searchFields.length > 0)searchFields[0].focus();}, 0);});});function setSelect2(nodeSet) {nodeSet.select2({ dropdownAutoWidth: true, width: `
- `, function (e) {window.setTimeout(function () {var searchFields = $(`
- `/js/resultlist.js?2.0`
- `ResultListDoSearch(`
- `athletesearchpanel`
- `btn btn-primary float-end btnSearch`
- `btnSearch`
- `expandsearch_label`

## 2026 (event 16880)

- HTML sampled: 93121 bytes
- Forms: 0
- Selects: 8
- Relevant links: 57

- Select 1 attrs `{'name': None, 'class': 'form-control selectDistance'}`: 97077=CRAFT Ultra 60 k; 97078=Fogarolli trail 22 K; 97080=Duo Trail (relay 2 x 30 km); 97079=Söderberg & Sara 14K; 97076=Naturloppet 5km+
- Select 2 attrs `{'name': None, 'class': 'form-control selectGender'}`: A=Män/Kvinnor; M=Män; F=Kvinnor
- Select 3 attrs `{'name': None, 'class': ' form-control selectCategory selectCategory_97077', 'style': 'display:none;'}`: all=Alla; 45147=90-; 45148=85-89; 45149=80-84; 45150=75-79; 45151=70-74; 45152=65-69; 45153=60-64; 45154=55-59; 45155=50-54; 45156=45-49; 45157=40-44; 45158=35-39; 45159=30-34; 45160=25-29; 45161=20-24; 45162=18-19; 45163=16-17; 45164=14-15; 45165=12-13; 45166=0-11
- Select 4 attrs `{'name': None, 'class': ' form-control selectCategory selectCategory_97078', 'style': 'display:none;'}`: all=Alla; 45147=90-; 45148=85-89; 45149=80-84; 45150=75-79; 45151=70-74; 45152=65-69; 45153=60-64; 45154=55-59; 45155=50-54; 45156=45-49; 45157=40-44; 45158=35-39; 45159=30-34; 45160=25-29; 45161=20-24; 45162=18-19; 45163=16-17; 45164=14-15; 45165=12-13; 45166=0-11
- Select 5 attrs `{'name': None, 'class': ' form-control selectCategory selectCategory_97080', 'style': 'display:none;'}`: all=Alla; 45147=90-; 45148=85-89; 45149=80-84; 45150=75-79; 45151=70-74; 45152=65-69; 45153=60-64; 45154=55-59; 45155=50-54; 45156=45-49; 45157=40-44; 45158=35-39; 45159=30-34; 45160=25-29; 45161=20-24; 45162=18-19; 45163=16-17; 45164=14-15; 45165=12-13; 45166=0-11
- Select 6 attrs `{'name': None, 'class': ' form-control selectCategory selectCategory_97079'}`: all=Alla; 45147=90-; 45148=85-89; 45149=80-84; 45150=75-79; 45151=70-74; 45152=65-69; 45153=60-64; 45154=55-59; 45155=50-54; 45156=45-49; 45157=40-44; 45158=35-39; 45159=30-34; 45160=25-29; 45161=20-24; 45162=18-19; 45163=16-17; 45164=14-15; 45165=12-13; 45166=0-11
- Select 7 attrs `{'name': None, 'class': ' form-control selectCategory selectCategory_97076', 'style': 'display:none;'}`: all=Alla; 45147=90-; 45148=85-89; 45149=80-84; 45150=75-79; 45151=70-74; 45152=65-69; 45153=60-64; 45154=55-59; 45155=50-54; 45156=45-49; 45157=40-44; 45158=35-39; 45159=30-34; 45160=25-29; 45161=20-24; 45162=18-19; 45163=16-17; 45164=14-15; 45165=12-13; 45166=0-11
- Select 8 attrs `{'name': None, 'class': 'form-control selectCountry'}`: all=Alla länder; 9=Australien; 14=Belgien; 29=Canada; 37=Danmark; 45=England; 52=Finland; 53=Frankrig; 60=Grækenland; 67=Holland; 70=Indien; 72=Irak; 74=Irland; 75=Island; 77=Italien; 79=Japan; 84=Kina; 121=New Zealand; 128=Norge; 135=Peru; 137=Polen; 149=Serbien; 157=Spanien; 161=Sverige; 163=Sydafrika; 179=Tyskland; 181=Uganda; 182=Ukraine; 185=USA; 188=Venezuela

Link patterns:
- `/event/16880/app/results/{result_id}` × 50
- `/event/16880/app/results?page={page}` × 4
- `/event/16880/app` × 1
- `/event/16880/app/participants` × 1
- `/event/16880/app/results` × 1

Candidate endpoint strings:
- `#athletesearchpanel`
- `);$.ajax({url: `
- `);if (searchFields.length > 0)searchFields[0].focus();}, 0);});});function setSelect2(nodeSet) {nodeSet.select2({ dropdownAutoWidth: true, width: `
- `, function (e) {window.setTimeout(function () {var searchFields = $(`
- `/js/resultlist.js?2.0`
- `ResultListDoSearch(`
- `athletesearchpanel`
- `btn btn-primary float-end btnSearch`
- `btnSearch`
- `expandsearch_label`


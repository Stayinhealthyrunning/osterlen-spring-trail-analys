# Sportstiming client request structure

Source inspected: `https://www.sportstiming.dk/js/resultlist.js?2.0`

JavaScript size: 7416 bytes

Only request/configuration snippets are retained; the complete third-party script is not mirrored.

## Request-related snippets

- `function ResultListDoSearch(ordering, orderby) { var original = $.parseParams(document.location.search.substr(1)); var queryString = $.parseParams(document.location.search.substr(1)); // Round var roundSel = $('.selectDistance'); var round = ''; var hasSetSplit = false; var forceIndividual = false; if (roundSel.length > 0) { //"s" + i + "_" + round.Id round = roundSel.val(); if (round.indexOf("s") == 0 && round.indexOf("_") > 0) { queryString.split = round.substring(1, round.indexOf("_")); round = round.substring(round.indexOf("_") + 1, round.length); hasSetSplit = true; } else if (round.indexOf("i") == 0) { round = round.substring(1, round.length); forceIndividual = true; } else { delete queryString.split; } if (round == 'null') delete queryString.round; else queryString.round = round; } // Gender var genderSel = $('.selectGender'); if (genderSel.length > 0) { var gender = genderSel.val(); if (gender == 'A') delete queryString.gender; else queryString.gender = gender; } // Result category var resultCategory = $('.selectResultCategory_' + round).val(); if (resultCategory == 'all' || resultCategory == undefined) delete queryString.resultcategory; else queryString.resultcategory = resultCategory; // Age category var category = $('.selectCategory_' + round).val(); if (category == 'all' || category == undefined) delete queryString.category; else queryString.category = category; // …`
- `.selectDistance,.selectGender,.selectCountry,.selectResultCategory,.selectCategory,.selectWave,.selectCity,.selectYear,.selectTeamtype,.selectDiscipline,.selectSplit,.selectCount', $('.page-filter-bar,.searchHeader')).on('change', function () {`
- `.selectDistance');`
- `.selectGender,.selectCountry,.selectResultCategory,.selectCategory,.selectWave,.selectCity,.selectYear,.selectTeamtype,.selectDiscipline,.selectSplit,.selectCount', $('.page-filter-bar,.searchHeader')).on('change', function () {`
- `.selectGender');`
- `.selectCategory,.selectWave,.selectCity,.selectYear,.selectTeamtype,.selectDiscipline,.selectSplit,.selectCount', $('.page-filter-bar,.searchHeader')).on('change', function () {`
- `.selectCategory_' + round).val();`
- `.selectCountry,.selectResultCategory,.selectCategory,.selectWave,.selectCity,.selectYear,.selectTeamtype,.selectDiscipline,.selectSplit,.selectCount', $('.page-filter-bar,.searchHeader')).on('change', function () {`
- `.selectCountry').val();`

## Relevant string literals

- `.btnSearch`
- `.page-filter-bar`
- `.searchHeader`
- `.selectDistance,.selectGender,.selectCountry,.selectResultCategory,.selectCategory,.selectWave,.selectCity,.selectYear,.selectTeamtype,.selectDiscipline,.selectSplit,.selectCount`
- `.page-filter-bar,.searchHeader`
- `.selectDistance`
- `)
            delete queryString.round;
        else
            queryString.round = round;
    }

    // Gender
    var genderSel = $(`
- `);
    if (genderSel.length > 0) {
        var gender = genderSel.val();
        if (gender == `
- `)
            delete queryString.gender;
        else
            queryString.gender = gender;
    }

    // Result category
    var resultCategory = $(`
- ` + round).val();
    if (resultCategory == `
- ` || resultCategory == undefined)
        delete queryString.resultcategory;
    else
        queryString.resultcategory = resultCategory;

    // Age category
    var category = $(`
- ` + round).val();
    if (category == `
- `.txtSearch`
- `#athletesearchpanel`
- `).val();
    if (ignoreAdvancedSearch || ln == `
- `).val();
    if (ignoreAdvancedSearch || club == `
- `).val();
    if (ignoreAdvancedSearch || wave == `
- ` || wave == undefined)
        delete queryString.wave;
    else
        queryString.wave = wave;

    // Country
    var nation = $(`
- `).val();
    if (ignoreAdvancedSearch || nation == `

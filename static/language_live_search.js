function refresh(items) {
    for (let i = 0; i < items.length; i++) {
        $(items[i]).show()
    }

    $('#empty').hide();
}

function filter(word, items) {
    let length = items.length;
    let hidden = 0;

    for (let i = 0; i < length; i++) {
        if (items[i].value.toLowerCase().startsWith(word.toLowerCase())) {
            $(items[i]).show()
        } else {
            $(items[i]).hide();
            hidden++
        }
    }

    if (hidden === length) {
        $('#empty').text("Add a new language: " + word);
        $('#empty').show();
    } else {
        $('#empty').hide();
    }
}

function language_live_search() {
    $('#empty').hide();
    $('#clear').hide();

    let items = document.getElementsByClassName("dropdown-item");

    window.addEventListener('input', function () {
        filter(document.getElementById("language").value.trim(), items)
    });

    $('#menuItems').on('click', '.dropdown-item', function () {
        document.getElementById("language").value = $(this)[0].value;
        $("#language").dropdown('toggle');
        document.getElementById("language").readOnly = true;
        $('#clear').show();
        $('#dropdown_menu').hide();
    });

    $('#clear').click(function () {
        document.getElementById("language").value = "";
        document.getElementById("language").readOnly = false;
        $('#clear').hide();
        $('#dropdown_menu').show();
        refresh(items);
    });

    $('#empty').click(function () {
        document.getElementById("language").readOnly = true;
        $('#clear').show();
        $('#dropdown_menu').hide();
    });
}
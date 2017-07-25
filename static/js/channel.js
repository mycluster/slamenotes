/**
 * JavaScript/jQuery code needed for channels
 */

/** Note output **/

var MONTH_ABBRS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function outputNote(note) {
    var already_exists = $("#note-" + note.pk).length !== 0; // Note in question exists in the DOM
    var have_text = note.fields.body_text !== ""; // We have text for the note in question

    if (!already_exists && have_text) { // Create new note element
        var noteElement = $("<article></article>", {
            id: "note-" + note.pk,
            "class": "note",
            tabindex: "0"
        });

        // Generate the note body
        var noteBody = $("<div></div>", {
            "class": "note-body"
        });
        noteBody.data('raw', note.fields.body_text);

        var noteParagraph = $("<p></p>", {
            html: note.fields.body_text
        });
        noteBody.append(noteParagraph);

        commonmarkParse(noteBody);

        noteElement.append(noteBody);


        // Generate the note meta

        var noteMeta = $("<p></p>", {
            "class": "note-meta clearfix"
        });

        // Generate the note author if sent
        if ("author" in note.fields) {
            if (note.fields.author == user.email) var author = "You"; else var author = note.fields.author;
            var noteAuthor = $("<span></span>", {
                "class": "note-author",
                html: author + ",&nbsp;"
            });
            noteMeta.append(noteAuthor);
        }

        // Generate the note date
        var today = new Date();
        var createdDate = new Date(note.fields.created_date);

        var noteDate = $("<span></span>", {
            "class": "note-date"
        });

        var timeHTML = "";
        if (createdDate.getFullYear() == today.getFullYear()    // Note was created today
            && createdDate.getMonth() == today.getMonth()
            && createdDate.getDay() == today.getDay()) {

            var hoursDiff = today.getHours() - createdDate.getHours();
            var minsDiff = today.getMinutes() - createdDate.getMinutes();
            var secsDiff = today.getSeconds() - createdDate.getSeconds();
            if (minsDiff < 0) {
                minsDiff += 60;
                hoursDiff -= 1;
            }
            if (secsDiff < 0)
                minsDiff -= 1;

            if (hoursDiff > 0) { // Output hour
                timeHTML += hoursDiff + " hour";
                if (hoursDiff != 1) // (s)
                    timeHTML += "s";
                if (minsDiff != 0)
                    timeHTML += ", ";
            }
            if ((hoursDiff > 0 && minsDiff > 0) || hoursDiff == 0) { // Output minute
                timeHTML += minsDiff + " minute";
                if (minsDiff != 1) // (s)
                    timeHTML += "s";
            }
        }
        else {  // Note was not created today
            timeHTML += MONTH_ABBRS[createdDate.getMonth()] + " ";
            if (createdDate.getDay() < 10) // Precede day number with 0 if single digit
                timeHTML += "0";
            timeHTML += createdDate.getDay();
            if (today.getYear() != createdDate.getYear()) // Note was not created this year
                timeHTML += ", " + createdDate.getYear();
        }

        // Generate the time tag
        var noteDateTime = $("<time></time>", {
            datetime: note.fields.created_date,
            html: timeHTML
        });

        noteDate.append(noteDateTime);
        noteMeta.append(noteDate);

        // Generate the note comments
        var noteComments = $("<span></span>", {
            "class": "note-comments",
            html: "0 comments"
        });
        noteMeta.append(noteComments);

        // Generate the note actions

        var noteActions = $("<span></span>", {
            "class": "note-actions"
        });

        if ("author" in note.fields && (note.fields.author == user.email || user.is_superuser)) {
            // This is one of user's notes (or user is a superuser), display appropriate actions
            var noteEdit = $("<a></a>", {
                "class": "note-edit fa fa-pencil",
                href: "#",
                role: "button",
                "aria-label": "edit"
            });
            noteActions.append(noteEdit);

            var noteEditCancel = $("<a></a>", {
                "class": "note-edit-cancel fa fa-times",
                href: "#",
                role: "button",
                "aria-label": "cancel edit"
            });
            noteActions.append(noteEditCancel);

            var noteDelete = $("<a></a>", {
                "class": "note-delete fa fa-trash",
                href: AJAX_URL + "?action=delete&note=" + note.pk,
                role: "button",
                "aria-label": "delete"
            });
            noteActions.append(noteDelete);
        }

        noteMeta.append(noteActions);

        noteElement.append(noteMeta);

        $('#results').prepend(noteElement);
    }
    else if (already_exists && have_text) { // Update note
        var theNote = $("#note-" + note.pk + " .note-body");
        theNote.empty();

        var noteParagraph = $("<p></p>", {
            html: note.fields.body_text
        });

        theNote.data('raw', noteParagraph.text());
        theNote.append(noteParagraph);

        commonmarkParse(theNote);
    }
    else if (already_exists && !have_text) { // Delete note
        $("#note-" + note.pk).remove();
    }
    else { // Do nothing, note was created and deleted before update occurred.
    }
}

/** AJAX functionality **/

function ajaxPostForm() {
    $.ajax({
       type: "POST",
       url: AJAX_URL,
       data: $("#note-form").serialize(),
       success: function() {
           ajaxSingleUpdate();
           $('#id_body_text').val('');
       }
     });
}
$("#note-post").click( function(event){
    event.preventDefault();
    ajaxPostForm();
});

function ajaxLiveUpdate() {
    var potential_new_update_time = new Date();
    $.ajax({
        url: AJAX_URL
            + '?action=load&channel=' + CHANNEL + '&session=all&modified_date='
            + encodeURIComponent(last_update.toISOString()),
        dataType: 'json',
        success: function(notes) {
            notes_changes = notes;

            var empty = $.isEmptyObject(notes_changes);
            $("#update-indicator")[ !empty ? 'show' : 'hide' ]();
            if (empty)
                last_update = potential_new_update_time;
        },
        complete: function() {
            // Schedule the next request in 5 seconds
            setTimeout(ajaxLiveUpdate, 5 * 1000);
        }
    });
}

function ajaxSingleUpdate() {
    $.ajax({
        url: AJAX_URL
            + '?action=load&channel=' + CHANNEL + '&session=all&modified_date='
            + encodeURIComponent(new Date(last_update - 60000).toISOString()), // 60000ms = 1min
        dataType: 'json',
        success: function(notes) {
            updateNotes(notes);
        }
    });
}

function updateNotes(notes) {
    $("#update-indicator")['hide']();
    last_update = new Date();
    for (var i in notes) {
        outputNote(notes[i]);
    }
    applyNoteActions();
}
$("#update-indicator a").click( function(event){
    event.preventDefault();
    updateNotes(notes_changes);
});

/** Note buttons **/

function noteEdit (id) {
    var the_note = $('#note-' + id);
    $('.editing').removeClass('editing');
    the_note.addClass('editing');

    var edit_form = $('#note-edit-form');
    var edit_form_textarea = $('#edit_body_text');

    edit_form.appendTo(the_note);
    edit_form.attr('action', AJAX_URL + '?action=edit&note=' + id);

    $("#note-edit-post").off('click').click( function(event){
        event.preventDefault();
        ajaxEditNote(AJAX_URL + '?action=edit&note=' + id);
    });

    edit_form_textarea.val(the_note.find(".note-body").data("raw"));
    edit_form_textarea.change();
}

function noteEditCancel () {
    var invis_holder = $('#invis-edit-form');
    $('.editing').removeClass('editing');

    var edit_form = $('#note-edit-form');
    var edit_form_textarea = $('#edit_body_text');
    edit_form.appendTo(invis_holder);
    edit_form_textarea.val('');
}

function ajaxEditNote(href) {
    $.ajax({
       type: "POST",
       url: href,
       data: $("#note-edit-form").serialize(),
       success: function() {
           ajaxSingleUpdate();
           noteEditCancel();
       }
     });
}

function noteDelete (id) {
    var the_note = $('#note-' + id);
    $('.deleting').removeClass('deleting');
    the_note.addClass('deleting');

    var prompt = $('#note-delete-prompt');
    prompt.appendTo(the_note);

    $("#note-delete-proceed").off('click').click( function(event){
        event.preventDefault();
        prompt.appendTo($('#invis-deletion-container'));
        ajaxDeleteNote(AJAX_URL + '?action=delete&note=' + id);
    });
}

function noteDeleteCancel () {
    var invis_holder = $('#invis-deletion-container');
    $('.deleting').removeClass('deleting');

    $('#note-delete-prompt').appendTo(invis_holder);
}
$("#note-delete-cancel").click(noteDeleteCancel);

function ajaxDeleteNote(href) {
    $.ajax({
        url: href,
        success: function() {ajaxSingleUpdate();}
    });
}

function applyNoteActions () {
    $(".note-edit").off( "click" ).click( function(event){
        event.preventDefault();
        noteEdit($(this).closest('.note').attr('id').split("note-")[1]);
    });
    $(".note-delete").off( "click" ).click( function(event){
        event.preventDefault();
        noteDelete($(this).closest('.note').attr('id').split("note-")[1]);
    });
    $(".note-edit-cancel").off( "click" ).click( function(event){
        event.preventDefault();
        noteEditCancel();
    });
}

/** Commonmark functionality **/

function commonmarkParse (element) {
    var reader = new commonmark.Parser();
    var writer = new commonmark.HtmlRenderer({smart: true, safe: true});
    var parsed = reader.parse($(element).text());
    $(element).html(writer.render(parsed));
}
function commonmarkParseAll () {
    $(".note-body").each(function (i, obj) {
        $(this).data('raw', $(this).text());
        commonmarkParse(this);
    });
}


/** Sort notes functionality **/


(function( $ ) {
    $.sortByDate = function( elements, order ) {
        var arr = [];
        elements.each(function() {
            var obj = {},
                $el = $( this ),
                time = $el.find( "datetime" ).text(),
                date = new Date( $.trim( time ) ),
                timestamp = date.getTime();
                obj.html = $el[0].outerHTML;
                obj.time = timestamp;
                arr.push( obj );
        });
        var sorted = arr.sort(function( first, second ) {
            if ( order == "ASC" ) {
                return first.time > second.time;
            }
            else {
                return first.time < second.time;
            }
        });
        return sorted;
    };
    $(function() {
        var $newer = $( "#newer" ),
            $older = $( "#older" ),
            $content = $( "#results" ),
            $elements = $( ".note" );
            $newer.click(function() {
                var elements = $.sortByDate( $elements, "DESC" );
                var html = "";
                for ( var i = 0; i < elements.length; ++i ) {
                    html += elements[i].html;
                }
                $content[0].innerHTML = html;
                $( this ).addClass( "selected" ).
                siblings().
                removeClass( "selected" );
                return false;
            });
            $older.click(function() {
                var elements = $.sortByDate( $elements, "ASC" );
                var html = "";
                for ( var i = 0; i < elements.length; ++i ) {
                    html += elements[i].html;
                }
                $content[0].innerHTML = html;
                $( this ).addClass( "selected" ).
                siblings().
                removeClass( "selected" );
                return false;
            });
    });
})( jQuery );

/** Search functionality **/

$("#note-search").on("keyup", function() {
    var g = $(this).val().toLowerCase();
    $(".note .note-body p").each(function() {
        var s = $(this).text().toLowerCase();
        $(this).closest('.note')[ s.indexOf(g) !== -1 ? 'show' : 'hide' ]();
    });
});

$("#channel-search").on("keyup", function() {
    var g = $(this).val().toLowerCase();
    $(".channel").each(function() {
        var s = $(this).text().toLowerCase();
        $(this)[ s.indexOf(g) !== -1 ? 'show' : 'hide' ]();
    });
});

/** Sidebar button functionality **/

$("#courses-menu-toggle").click(function() {
    $(".sidebar-container").toggleClass('courses-menu-open');
});

$("#collapse-menu").click(function() {
    $(document.body).toggleClass('menu-closed');
});

$("#expand-menu").click(function() {
    $(document.body).toggleClass('menu-closed');
});

/** Add class overlay functionality **/

$("#courses-add").on("click", function () {
    $("body").addClass("overlay-active");
});

$("#channel-overlay-close").on("click", function () {
    $("body").removeClass("overlay-active");
});

var channel_overlay = $(".channel-overlay");

$("#overlay-tab-search").on("click", function () {
    channel_overlay.removeClass("channel-creating");
});

$("#overlay-tab-create").on("click", function () {
    channel_overlay.addClass("channel-creating");
});

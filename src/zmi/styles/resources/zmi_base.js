// zmi_base.js

// HELPERS

// Simple Check for Absolute URL
function isURL(str) {
	return /^(?:\w+:)?\/\/\S*$/.test(str);
};
function isSafari() {
	return /^((?!chrome).)*safari/i.test(navigator.userAgent);
}

// NAVBAR-FUNCTIONS

// [1] Add New Object Item (with Modal Dialog)
function addItem( elm, base_url ) {
	var zmi_dialog = elm.options[elm.selectedIndex].getAttribute('data-dialog');
	// e.g. manage_addProduct/OFSP/folderAdd
	var url_action =  elm.options[elm.selectedIndex].value;
	// http://localhost/myfolder/manage_addProduct/OFSP/folderAdd
	var url_full = base_url + '/' + url_action;
	var parts = url_action.split('/');
	// folderAdd
	var action = parts[parts.length-1];
	// OFSP
	var product = parts[parts.length-2];
	// http://localhost/myfolder/manage_addProduct/OFSP/
	var modal_form_base = url_full.slice(0, -action.length);
	var modal_body_url = url_full + '?zmi_dialog=' + zmi_dialog ;

	// Inserting Without Modal Dialog
	var no_modal_dialog = {
		'product':[
			'CMFPlone',
			'CMFEditions',
			'zms',
		]
	};

	if ( zmi_dialog != 'modal' || $.inArray(product, no_modal_dialog['product']) !== -1 ) {
		window.location.href = url_full;
		return
	}

	// SHOW MODAL DIALOG
	$('#zmi-modal').modal('show');
	$('#zmi-modal').modal({ focus: true });
	$('#zmi-modal .modal-body').attr('data-add_type', action);
	// Load Modal Form by AJAX
	$('#zmi-modal .modal-body').load(modal_body_url, function(responseTxt, statusTxt, xhr) {
		if(statusTxt == "error") {
			window.location.href = url_full;
				return;
		}

		//Modify Form Action for Modal Use
		$( '#zmi-modal form' ).each( function() {
			var former_action = $( this ).attr( 'action' );
			var modal_form_url = isURL(former_action) ? former_action : modal_form_base + former_action;
			$( this ).attr( 'action', modal_form_url );
		});

		fix_ancient_modal_gui();
		fix_modern_modal_gui();
	});
	// Clean up Modal DOM on Close
	$('#zmi-modal').on('hide.bs.modal', function (event) {
		$('#zmi-modal .modal-header h2').remove();
		$('#zmi-modal .modal-body').empty();
	});
}


// [2] GUI FIX: Add Minimal Style Patches to Ancient Zope Forms
function fix_ancient_gui() {
	if ( 0 !== $('main').length ) {
		return;
	}
	// WRAP FORM ELEMENT with fluid-container (if missing)
    $('body>form,body>textarea,body>table,body>h2,body>h3,body>p,body.zmi-Generic-Setup-Tool>div:not(.modal)').wrapAll('<main class="container-fluid zmi-patch"></main>');
	// ADD BOOTSTRAP CLASSES
	$('input[type="text"], input[type="file"], textarea, select').addClass('form-control zmi-patch');
	$('input[type="submit"]').addClass('btn btn-primary zmi-patch');
	$('textarea[name*=":text"]').addClass('zmi-code');
	$('table').addClass('table zmi-patch');
}

// [3] GUI FIX FOR MODAL DIALOG: Add Minimal Style Patches to Ancient Zope Forms
function fix_ancient_modal_gui() {
	if ( 0 === $('.modal-body main').length ) {
		$('.modal-body>form,.modal-body>table,.modal-body>h2,.modal-body>h3,.modal-body>p,.modal-body>i.zmi-help-icon').wrapAll('<main class="container-fluid zmi-patch"></main>');
		// ADD BOOTSTRAP CLASSES
		$('.modal-body input[type="text"],.modal-body input[type="file"],.modal-body textarea,.modal-body select').addClass('form-control zmi-patch');
		$('.modal-body input[type="submit"]').addClass('btn btn-primary zmi-patch');
		$('.modal-body textarea[name*=":text"]').addClass('zmi-code');
		$('.modal-body table').addClass('table zmi-patch');
	}
}

function fix_modern_modal_gui() {
	// Shift Title to Modal Header
	$('#zmi-modal .modal-body h2').detach().prependTo('#zmi-modal .modal-header');

	// Aggregate multiple Help-Paragraphs
	if ( $('#zmi-modal .modal-body p.form-help').length > 1) {
		var help_text = $('#zmi-modal .modal-body p.form-help').text();
		var help_text_html = '<p class="form-help">' + help_text +'</p>';
		$('#zmi-modal .modal-body p.form-help').remove();
		if ( 0 === $('.modal-body main').length ) {
			$('#zmi-modal .modal-body').prepend(help_text_html);
		} else {
			$('#zmi-modal .modal-body main').prepend(help_text_html);
		}
	}
	$('#zmi-modal .modal-body p.form-help').before('<i title="Help" class="zmi-help-icon fas fa-question-circle" onclick="$(\'#zmi-modal .form-help\').toggle();$(this).toggleClass(\'active\')"></i>');
	$('#zmi-modal .modal-body p.form-help').hide();
}

// +++++++++++++++++++++++++++++++
// +++ Ajax.org Cloud9 Editor
// +++ http://ace.ajax.org
// +++++++++++++++++++++++++++++++
function show_ace_editor() {
	$('#content').wrap('<div id="editor_container" class="form-group"></div>');
	$('#content').before('<div id="editor">ace editor text</div>');
	var dom = ace.require("ace/lib/dom");
	// add command to all new editor instances
	ace.require("ace/commands/default_commands").commands.push({
		name: "Toggle Fullscreen",
		bindKey: "F10",
		exec: function(editor) {
			var fullScreen = dom.toggleCssClass(document.body, "fullScreen");
			dom.setCssClass(editor.container, "fullScreen", fullScreen);
			editor.setAutoScrollEditorIntoView(!fullScreen);
			editor.resize();
		}
	});
	// @see https://github.com/ajaxorg/ace/wiki/Embedding---API
	$("textarea#content").hide();
	editor = ace.edit("editor");
	var value = $("textarea#content").val();
	var content_type = $("input#contenttype").val();
	if ( $("textarea#content").attr('data-contenttype') ) {
		content_type = $("textarea#content").attr('data-contenttype');
	}
	if (typeof content_type === "undefined" || ! content_type || content_type === 'text/x-unknown-content-type') {
		var absolute_url = $("span#absolute_url").text();
		var id = absolute_url.substr(absolute_url.lastIndexOf("/")+1);
		if (id.endsWith(".css")) {
			content_type = "text/css";
		}
		else if (id.endsWith(".less")) {
			content_type = "text/less";
		}
		else if (id.endsWith(".js")) {
			content_type = "text/javascript";
		}
		else {
			content_type = "text/html";
		}
	}
	if ( 0 === value.indexOf("<html") && content_type != 'dtml') {
		content_type = "text/html";
	}
	if ( 0 === value.indexOf("<?xml") || value.indexOf("tal:") >= 0) {
		content_type = "text/xml";
	}
	if ( 0 === value.indexOf("#!/usr/bin/python") || 0 === value.indexOf("## Script (Python)") ) {
		content_type = "python";
	}
	var mode = "text";
	if (content_type == "html" || content_type == "text/html") {
		mode = "html";
	}
	else if (content_type == "text/css" || content_type == "application/css" || content_type == "application/x-css") {
		mode = "css";
	}
	else if (content_type == "text/less") {
		mode = "less";
	}
	else if (content_type == "text/javascript" || content_type == "application/javascript" || content_type == "application/x-javascript") {
		mode = "javascript";
	}
	else if (content_type == "text/xml") {
		mode = "xml";
	}
	else if (content_type == "python") {
		mode = 'python';
	}
	else if (content_type == "sql") {
		mode = 'sql';
	}
	else if (content_type == "json") {
		mode = 'json';
	}
	else if (content_type == "dtml") {
		mode = 'markdown';
	}
	editor.setTheme("ace/theme/eclipse");
	editor.getSession().setMode('ace/mode/'+mode);
	editor.getSession().setValue(value);
	editor.getSession().on("change",function() {
		$("textarea#content").val(editor.getSession().getValue()).change();
	});
}

// ++++++++++++++++++++++++++
// EXECUTE ON DOCUMENT READY
// ++++++++++++++++++++++++++
$(function() {

	// SHOW ACE EDITOR
	if ($('#content').length > 0 ) {
		show_ace_editor();
	}

	// EXECUTE DESIGN WORKAROUNDS
	// Needed until ALL GUI Forms are Bootstrap Conformant
	fix_ancient_gui();

	// EXECUTE FUNCTIONAL WORKAROUNDS
	//  empty for the moment

	if (!window.matchMedia || (window.matchMedia("(max-width: 767px)").matches)) {
		$('.zmi header.navbar li.zmi-authenticated_user').tooltip({'placement':'bottom'});
	}
	
	// EXPAND LONG ERROR ALERTS
	if ($('main.container-fluid .alert pre').text().split(/\n/).length > 2) {
		$('main.container-fluid .alert pre').addClass('alert_xl');
		$('main.container-fluid .alert pre').click( function() {
			$(this).toggleClass('fullheight');
		})
	}

	// COMPRESS USER PERMISSIONS TABLE SIZE
	if ($('body.zmi-manage_access').length !== 0) {
		function resize_permissions_table() {
			if ( $('#table-permissions').width() > $(window).width() || isSafari() ) {
				$('#table-permissions').addClass('compress');
			}
		}
		resize_permissions_table();
		$(window).resize(function() {
			resize_permissions_table();
		})
	}
});

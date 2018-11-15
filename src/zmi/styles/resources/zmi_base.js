// zmi_base.js

// NAVBAR-FUNCTIONS

function setupShowHideTreeView() {
	/*
	Disable the show sidebar button if the sidebar cannot be shown
	without navigating away from the current view.
	
	It would be cool to get rid of this, but that would require
	reworking the TreeTagView to understand that it could show the 
	elements above the current object if it is not a folderish thing.
	*/
	var $li = $('#toggle_menu');
	if (0 === $li.length) {
		return // no menu toggle on this page
	}
	
	var $a = $li.find('a');
	// var isInFrameset = window.parent.location.href.endsWith('/manage');
	var isShowingFrameset = window !== window.parent;
	var isFolderish = !! $li.data().is_folderish
	if (isShowingFrameset) {
		$a.attr('href', 'manage_main')
	}
	else {
		if ( isFolderish ) {
			$a.attr('href', 'manage')
		}
		else {
			$li.attr('title', $li.attr('data-title_inactive'));
			$a.addClass('disabled');
		}
	}
}

// [2] Add New Object Item (with Modal Dialog)
function addItem( elm, base_url ) {
	// e.g. manage_addProduct/OFSP/folderAdd
	var url_action =  elm.options[elm.selectedIndex].value;
	// http://localhost/myfolder/manage_addProduct/OFSP/folderAdd
	var url_full = base_url + '/' + url_action;
	var parts = url_action.split('/');
	// folderAdd
	var action = parts[parts.length-1];
	// http://localhost/myfolder/manage_addProduct/OFSP/
	var modal_form_base = url_full.slice(0, -action.length);
	var modal_body_url = url_full + '?zmi_dialog=modal';

	// List of Object Types Inserting Without Modal Dialog
	var no_modal_dialog = [
		'manage_addRegistry',
		'manage_addUserFolder',
		'manage_addErrorLog',
		'manage_addVirtualHostMonster',
		'manage_addzmsform',
		'addPluggableAuthService',
	];

	if ( $.inArray(action, no_modal_dialog) !== -1 ) {
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
			var modal_form_url = modal_form_base + $( this ).attr( 'action' );
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
	$('body>form,body>textarea,body>table,body>h2,body>p').wrapAll('<main class="container-fluid zmi-patch"></main>');
	// ADD BOOTSTRAP CLASSES
	$('input[type="text"], input[type="file"], textarea, select').addClass('form-control zmi-patch');
	$('input[type="submit"]').addClass('btn btn-primary zmi-patch');
	$('textarea[name*=":text"]').addClass('zmi-code');
	$('table').addClass('table zmi-patch');
}

// [3] GUI FIX FOR MODAL DIALOG: Add Minimal Style Patches to Ancient Zope Forms
function fix_ancient_modal_gui() {
	if ( 0 === $('.modal-body main').length ) {
		$('.modal-body>form,.modal-body>table,.modal-body>h2,.modal-body>p,.modal-body>i.zmi-help-icon').wrapAll('<main class="container-fluid zmi-patch"></main>');
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
		$('#zmi-modal .modal-body p.form-help').remove();
		$('#zmi-modal .modal-body').prepend('<p class="form-help">' + help_text +'</p>');
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
	var dom = require("ace/lib/dom");
	// add command to all new editor instances
	require("ace/commands/default_commands").commands.push({
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
	if ( 0 === value.indexOf("<html")) {
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
	// [1] Showing some Menu Elements only on List Page as Active
	if ($('.nav a[href="manage_findForm"]').length > 0 ) {
		$('#addItemSelect').removeClass('disabled');
		$('#addItemSelect').removeAttr('disabled');
		$('#addItemSelect').attr( 'title', $('#addItemSelect').attr('data-title-active') );
	} else {
		$('#addItemSelect').addClass('disabled');
		$('#addItemSelect').attr('disabled','disabled');
		$('#addItemSelect').attr( 'title', $('#addItemSelect').attr('data-title-inactive') );
	}
	
	setupShowHideTreeView()

	if (!window.matchMedia || (window.matchMedia("(max-width: 767px)").matches)) {
		$('.zmi header.navbar li.zmi-authenticated_user').tooltip({'placement':'bottom'});
	}

});


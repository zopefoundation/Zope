// zmi_base.js

// NAVBAR-FUNCTIONS

// [1] Toggle Sitemap
function toggle_menu() {
	if (document.referrer.endsWith('/manage')) {
		window.parent.location.href="manage_main";
	} else {
		window.parent.location.href="manage";
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


// ++++++++++++++++++++++++++++++++++++++++
// DESIGN-FUNCTIONS
// Ex-post Design-Fixes for Non-Bootstrap-
// Conformant GUI Pages and Missing Icons
// ++++++++++++++++++++++++++++++++++++++++

// [1] ICON FIX: As long as not set systematically in the class definitions
 function fix_zmi_icons() {
	 var zmi_icons = {
		"User Folder":{ "title":"Access Control List", "class":"fa fa-user-friends" }, // templated
		"UserFolder":{ "title":"Access Control List", "class":"fa fa-user-friends" },
		"Pluggable Auth Service":{ "title":"Pluggable Auth Service", "class":"fa fa-users-cog" },
		"User":{ "title":"User", "class":"fa fa-user" },
		"Temporary Folder":{ "title":"Temporary Folder", "class":"far fa-hdd" },
		"Filesystem Directory View":{ "title":"Filesystem Directory View", "class":"far fa-folder-open" },
		"Ordered":{ "title":"Folder (Ordered)", "class":"far fa-folder zmi-icon-folder-ordered" }, // templated
		"Folder":{ "title":"Folder", "class":"far fa-folder" },
		"Script":{ "title":"Script (Python)", "class":"fa fa-terminal" },
		"External Method":{ "title":"External Python Method", "class":"fa fa-external-link-square-alt" },
		"DTML Document":{ "title":"DTML Document", "class":"far fa-file-alt" },
		"DTML Method":{ "title":"DTML Method", "class":"far fa-file-alt" },
		"Page Template":{ "title":"Page Template", "class":"far fa-file-code" },
		"File":{ "title":"File Object", "class":"far fa-file-archive" },
		"Mail":{ "title":"Mail Folder", "class":"far fa-envelope" },
		"Image":{ "title":"Image", "class":"far fa-file-image" },
		"Control":{ "title":"Control Panel", "class":"fa fa-cog" },
		"Database":{ "title":"Database", "class":"fa fa-database" },
		"ZSQLiteDA":{ "title":"Database", "class":"fa fa-database" },
		"ZMySQLDA":{ "title":"MySQL-Database Adapter", "class":"fa fa-database" },
		"Product":{ "title":"Installed Product", "class":"fa fa-gift" },
		"ZSQL":{ "title":"ZSQL-Method", "class":"far fa-puzzle-piece" },
		"Debug Manager":{ "title":"Debug Manager", "class":"fas fa-bug" },
		"Site Error Log":{ "title":"Site Error Log", "class":"fas fa-bug" },
		"Browser Id Manager":{ "title":"Browser Id Manager", "class":"far fa-id-card" },
		"ZMS":{ "title":"ZMS Root", "class":"fas fa-home" },
		"ZMSObject.png":{ "title":"ZMS Content", "class":"far fa-file" },
		"Monster":{ "title":"Virtual Host Monster", "class":"fa fa-code-branch" },
		"ZCatalogIndex":{ "title":"ZCatalogIndex", "class":"far fa-list-alt" },
		"ZCatalog":{ "title":"ZCatalog", "class":"fa fa-search" },
		"Session Data Manager":{ "title":"Session Data Manager", "class":"far fa-clock" },
		"Cookie Crumbler":{ "title":"Cookie Crumbler", "class":"fa fa-cookie-bite" },
		"Broken object":{ "title":"Broken object", "class":"fas fa-ban text-danger" }
	};

	// PROCESS Object Icons
	for ( var i in zmi_icons ) {
		var i_name = i;
		var i_title =zmi_icons[i].title;
		var i_class =zmi_icons[i].class;
		if ( $('i[title*="'+i_name+'"]').hasClass('zmi_icon-broken') ) {
		 	i_class += ' zmi_icon-broken';
		}
		$('i[title*="'+i_name+'"]').replaceWith('<i data-title="'+i_title+'" class="'+i_class+'"></i>');
	}
	// PROCESS Other Icons
	$('i[title*="/p_/pl"]').replaceWith('<i data-title="Expand..." class="far fa-plus-square"></i>');
	$('i[title*="/p_/mi"]').replaceWith('<i data-title="Collapse..." class="far fa-minus-square"></i>');
	$('i[title*="/p_/davlocked"]').replaceWith('<i data-title="WebDAV" class="fa fa-retweet"></i>');
	$('img[src*="misc_"]').replaceWith('<i class="fa fa-circle-blank"></i>');
	$('img[src*="zms_"]').replaceWith('<i class="fa fa-circle-blank"></i>');
	$('#menu_tree td[width="16"] a:contains("+")').html(('<i title="Expand..." class="fas fa-caret-right text-muted"></i>'));
	$('#menu_tree td[width="16"] a:contains("-")').html(('<i title="Collapse..." class="fas fa-caret-down text-muted"></i>'));
	$('a[href*="HelpSys"]').empty()
		.append('<i class="fa fa-question-sign"></i>')
		.css('border-color','transparent');
}

// [2] GUI FIX: Add Minimal Style Patches to Ancient Zope Forms
function fix_ancient_gui() {
	// WRAP FORM ELEMENT with fluid-container (if missing)
	if ( 0 === $('main').length ) {
		$('body>form,body>textarea,body>table,body>h2,body>p').wrapAll('<main class="container-fluid zmi-patch"></main>');
		// ADD BOOTSTRAP CLASSES
		$('input[type="text"], input[type="file"], textarea, select').addClass('form-control zmi-patch');
		$('input[type="submit"]').addClass('btn btn-primary zmi-patch');
		$('textarea[name*=":text"]').addClass('zmi-code');
		$('table').addClass('table zmi-patch');
	}
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
	fix_zmi_icons();
	fix_ancient_gui();

	// EXECUTE FUNCTIONAL WORKAROUNDS
	// [1] Showing some Menu Elements only on List Page as Active
	if ($('.nav a[href="manage_findForm"]').length > 0 ) {
		$('#addItemSelect, #toggle_menu').css('opacity',1);
		$('#addItemSelect').removeAttr('disabled');
		$('#addItemSelect').attr( 'title', $('#addItemSelect').attr('data-title-active') );
		$('#toggle_menu').attr( 'title', $('#toggle_menu').attr('data-title-active') );
	} else {
		$('#addItemSelect, #toggle_menu').css('opacity', 0.5);
		$('#addItemSelect').attr('disabled','disabled');
		$('#addItemSelect').attr( 'title', $('#addItemSelect').attr('data-title-inactive') );
		$('#toggle_menu').attr( 'title', $('#toggle_menu').attr('data-title-inactive') );
	}

	if (!window.matchMedia || (window.matchMedia("(max-width: 767px)").matches)) {
		$('.zmi header.navbar li.zmi-authenticated_user').tooltip({'placement':'bottom'});
	}

});


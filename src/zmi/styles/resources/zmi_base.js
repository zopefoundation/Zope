

// NAVBAR-FUNCTIONS
function toggle_menu() {
	if (document.referrer.endsWith('/manage')) {
		window.parent.location.href="manage_main";
	} else {
		window.parent.location.href="manage";
	};
}

function addItem( elm, url1 ) {
	var action =  elm.options[elm.selectedIndex].value;
	var add_type = action.split('/')[2];
	var win_url = url1 + '/' + action
	var modal_body_url = win_url + '?zmi_dialog=modal';

	// List of Object Types Inserting Without Form GUI
	var no_form_types = [
		'manage_addVirtualHostMonster',
		'manage_addRegistry'
	]
	
	if ( $.inArray(add_type, no_form_types) < 0 ) {
	// SHOW MODAL DIALOG
		$('#zmi-modal').modal('show');
		$('#zmi-modal').modal({ focus: true });
		$('#zmi-modal .modal-body').attr('data-add_type', add_type);
		// Load Modal Form by AJAX
		$('#zmi-modal .modal-body').load(modal_body_url);
		// Shift Titel to Modal Header
		$( document ).ajaxComplete(function() {
			$('#zmi-modal .modal-body h2').detach().prependTo('#zmi-modal .modal-header');
			// Why is this removing necessary..
			$('#zmi-modal .modal-body i').remove();
			// Aggregate multiple help-paragraphs
			if ( $('#zmi-modal .modal-body p.form-help').length > 1) {
				var help_text = $('#zmi-modal .modal-body p.form-help').text();
				$('#zmi-modal .modal-body p.form-help').remove();
				$('#zmi-modal .modal-body').prepend('<p class="form-help">' + help_text +'</p>');
			}
			$('#zmi-modal .modal-body p.form-help').before('<i title="Help" class="zmi-help-icon fas fa-question-circle" onclick="$(\'.form-help\').toggle();$(this).toggleClass(\'active\')"></i>');
			$('#zmi-modal .modal-body p.form-help').hide();
		});
		// Clean up Modal DOM on Close
		$('#zmi-modal').on('hide.bs.modal', function (event) {
			$('#zmi-modal .modal-header h2').remove();
			$('#zmi-modal .modal-body').empty();
		});
	} else {
	// REDIRECT TO NEW URL (WINDOW)
		window.location.href = win_url;
	}
}


// ++++++++++++++++++++++++++
// QUICKFIX OBJECT ICONS (as long as not set systematically in the class definitions)
// 1. ICON-DEFINITION-DICT:
// ++++++++++++++++++++++++++
var zmi_icons = {
	"User Folder":{ "title":"Access Control List", "class":"fa fa-user-friends" },
	"UserFolder":{ "title":"Access Control List", "class":"fa fa-user-friends" },
	"PluggableAuthService":{ "title":"Pluggable Auth Service", "class":"fa fa-users-cog" },
	"User":{ "title":"User", "class":"fa fa-user" },
	"TemporaryFolder":{ "title":"Folder", "class":"far fa-folder" },
	"Filesystem Directory View":{ "title":"Filesystem Directory View", "class":"far fa-folder-open" },
	"Ordered":{ "title":"Folder (Ordered)", "class":"far fa-folder zmi-icon-folder-ordered" },
	"Folder":{ "title":"Folder", "class":"far fa-folder" },
	"Script":{ "title":"Script (Python)", "class":"fa fa-terminal" },
	"ExternalMethod":{ "title":"External Python Method", "class":"fa fa-external-link-square" },
	"DTML Document":{ "title":"DTML Document", "class":"far fa-file-alt" },
	"DTML Method":{ "title":"DTML Document", "class":"far fa-file-alt" },
	"Page Template":{ "title":"Page Template", "class":"far fa-file-code" },
	"File":{ "title":"File Object", "class":"far fa-file-archive" },
	"Mail":{ "title":"Mail Folder", "class":"far fa-envelope" },
	"Image":{ "title":"Image", "class":"far fa-file-image" },
	"Control":{ "title":"Control Panel", "class":"fa fa-cogs" },
	"Database":{ "title":"Database", "class":"far fa-database" },
	"ZSQLiteDA":{ "title":"Database", "class":"far fa-database" },
	"ZMySQLDA":{ "title":"MySQL-Database Adapter", "class":"far fa-database" },
	"Product":{ "title":"Installed Product", "class":"fa fa-gift" },
	"ZSQL":{ "title":"ZSQL-Method", "class":"far fa-puzzle-piece" },
	"Debug Manager":{ "title":"Debug Manager", "class":"fas fa-bug" },
	"Site Error Log":{ "title":"Site Error Log", "class":"fas fa-bug" },
	"Browser Id Manager":{ "title":"Browser Id Manager", "class":"far fa-id-card" },
	"ZMS":{ "title":"ZMS Root", "class":"fas fa-home" },
	"ZMSObject.png":{ "title":"ZMS Content", "class":"far fa-file" },
	"Monster":{ "title":"Virtual Host Monster", "class":"fa fa-code-branch" },
	"ZCatalog":{ "title":"ZCatalog", "class":"far fa-search" },
	"Session Data Manager":{ "title":"Session Data Manager", "class":"fas fa-history" },
	"Cookie Crumbler":{ "title":"Cookie Crumbler", "class":"far fa-user-circle" },
	"Broken object":{ "title":"Broken object", "class":"fas fa-ban text-danger" }
}

// ++++++++++++++++++++++++++
// ON DOCUMENT READY
// ++++++++++++++++++++++++++
$(function() {

	// WRAP FORM ELEMENT with fluid-container (if missing)
	if ( $('main.container-fluid').length==0 ) {
		$('body>form,body>p').wrap('<main class="container-fluid"></main>');
	}

	// QUICKFIX OBJECT ICONS 
	// 2. EXECUTE ICON QUICKFIX
	for ( i in zmi_icons ) {
		var i_name = i;
		var i_title =zmi_icons[i].title;
		var i_class =zmi_icons[i].class;
		if ( $('i[title*="'+i_name+'"]').hasClass('icon-broken') ) {
			i_class += ' zmi-icon-broken'
		};
		$('i[title*="'+i_name+'"]').replaceWith('<i data-title="'+i_title+'" class="'+i_class+'"></i>');
	}

// OTHER ICONS
	$('i[title*="/p_/pl"]').replaceWith('<i data-title="Expand..." class="far fa-plus-square"></i>');
	$('i[title*="/p_/mi"]').replaceWith('<i data-title="Collapse..." class="far fa-minus-square"></i>');
	$('i[title*="/p_/davlocked"]').replaceWith('<i data-title="WebDAV" class="fa fa-retweet"></i>');
	$('img[src*="misc_"]').replaceWith('<i class="fa fa-circle-blank"></i>');
	$('img[src*="zms_"]').replaceWith('<i class="fa fa-circle-blank"></i>');
	$('#menu_tree td[width="16"] a:contains("+")').html(('<i title="Expand..." class="fas fa-caret-right text-muted"></i>'));
	$('#menu_tree td[width="16"] a:contains("-")').html(('<i title="Collapse..." class="fas fa-caret-down text-muted"></i>'));

// WORKAROUND: SHOW SOME MENUS ELEMENTS ONLY ON LIST PAGES AS ACTIVE
	if ($('.nav a[href="manage_findForm"]').length > 0 ) {
		$('#addItemSelect, #toggle_menu').css('opacity',1);
		$('#addItemSelect').removeAttr('disabled');
		$('#addItemSelect').attr( 'title', $('#addItemSelect').attr('data-title-active') );
		$('#toggle_menu').attr( 'title', $('#toggle_menu').attr('data-title-active') );
	} else {
		$('#addItemSelect, #toggle_menu').css('opacity',.5);
		$('#addItemSelect').attr('disabled','disabled');
		$('#addItemSelect').attr( 'title', $('#addItemSelect').attr('data-title-inactive') );
		$('#toggle_menu').attr( 'title', $('#toggle_menu').attr('data-title-inactive') );
	}

// HELP ICON
	$('a[href*="HelpSys"]').empty()
		.append('<i class="fa fa-question-sign"></i>')
		.css('border-color','transparent');

});


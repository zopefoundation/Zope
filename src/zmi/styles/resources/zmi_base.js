// zmi_base.js

// NAVBAR-FUNCTIONS

// [1] Toggle Sitemap
function toggle_menu() {
	if (document.referrer.endsWith('/manage')) {
		window.parent.location.href="manage_main";
	} else {
		window.parent.location.href="manage";
	};
}

// [2] Add New Object Item (with Modal Dialog)
function addItem( elm, base_url ) {
	var url_action =  elm.options[elm.selectedIndex].value;
	var url_full = base_url + '/' + url_action;
	var action = url_action.split('/')[url_action.split('/').length-1];
	var modal_form_base = url_full.split(action)[0];
	var modal_body_url = url_full + '?zmi_dialog=modal';

	// List of Object Types Inserting Without Modal Dialog 
	var no_modal_dialog = [
		'manage_addRegistry',
		'manage_addUserFolder',
		'manage_addErrorLog',
		'manage_addVirtualHostMonster',
		'manage_addzmsform'
	]

	// SHOW MODAL DIALOG	
	if ( $.inArray(action, no_modal_dialog) < 0 ) {
	// Deactivate for Testing Purposes:
	// if ( 1==0 ) {
		$('#zmi-modal').modal('show');
		$('#zmi-modal').modal({ focus: true });
		$('#zmi-modal .modal-body').attr('data-add_type', action);
		// Load Modal Form by AJAX
		$('#zmi-modal .modal-body').load(modal_body_url);
		// Shift Titel to Modal Header
		$( document ).ajaxComplete(function() {
			$('#zmi-modal .modal-body h2').detach().prependTo('#zmi-modal .modal-header');
			// STRANGE: Why is this Removing Necessary..
			$('#zmi-modal .modal-body i').remove();
			// Aggregate multiple Help-Paragraphs
			if ( $('#zmi-modal .modal-body p.form-help').length > 1) {
				var help_text = $('#zmi-modal .modal-body p.form-help').text();
				$('#zmi-modal .modal-body p.form-help').remove();
				$('#zmi-modal .modal-body').prepend('<p class="form-help">' + help_text +'</p>');
			}
			$('#zmi-modal .modal-body p.form-help').before('<i title="Help" class="zmi-help-icon fas fa-question-circle" onclick="$(\'#zmi-modal .form-help\').toggle();$(this).toggleClass(\'active\')"></i>');
			$('#zmi-modal .modal-body p.form-help').hide();

			//Modify Form Action for Modal Use
			$( '#zmi-modal form' ).each( function() {
				var modal_form_url = modal_form_base + $( this ).attr( 'action' );
				$( this ).attr( 'action', modal_form_url )
			})

			// GUI FIX FOR MODAL DIALOG: Add Minimal Style Patches to Ancient Zope Forms
			fix_ancient_modal_gui();
		});
		// Clean up Modal DOM on Close
		$('#zmi-modal').on('hide.bs.modal', function (event) {
			$('#zmi-modal .modal-header h2').remove();
			$('#zmi-modal .modal-body').empty();
		});
	} else {
	// REDIRECT TO NEW URL (WINDOW)
		window.location.href = url_full;
	}
}


// ++++++++++++++++++++++++++++++++++++++++
// DESIGN-FUNCTIONS
// Ex-post Design-Fixes for Non-Bootstrap-
// Conformant GUI Pages and Missing Icons
// ++++++++++++++++++++++++++++++++++++++++

// [1] ICON FIX: As long as not set systematically in the class definitions
 function fix_zmi_icons() {
	 var zmi_icons = {
		"User Folder":{ "title":"Access Control List", "class":"fa fa-user-friends" },
		"UserFolder":{ "title":"Access Control List", "class":"fa fa-user-friends" },
		"Pluggable Auth Service":{ "title":"Pluggable Auth Service", "class":"fa fa-users-cog" },
		"User":{ "title":"User", "class":"fa fa-user" },
		"Temporary Folder":{ "title":"Temporary Folder", "class":"far fa-hdd" },
		"Filesystem Directory View":{ "title":"Filesystem Directory View", "class":"far fa-folder-open" },
		"Ordered":{ "title":"Folder (Ordered)", "class":"far fa-folder zmi-icon-folder-ordered" },
		"Folder":{ "title":"Folder", "class":"far fa-folder" },
		"Script":{ "title":"Script (Python)", "class":"fa fa-terminal" },
		"External Method":{ "title":"External Python Method", "class":"fa fa-external-link-square-alt" },
		"DTML Document":{ "title":"DTML Document", "class":"far fa-file-alt" },
		"DTML Method":{ "title":"DTML Document", "class":"far fa-file-alt" },
		"Page Template":{ "title":"Page Template", "class":"far fa-file-code" },
		"File":{ "title":"File Object", "class":"far fa-file-archive" },
		"Mail":{ "title":"Mail Folder", "class":"far fa-envelope" },
		"Image":{ "title":"Image", "class":"far fa-file-image" },
		"Control":{ "title":"Control Panel", "class":"fa fa-cogs" },
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
	}
// PROCESS Object Icons
		for ( i in zmi_icons ) {
			var i_name = i;
			var i_title =zmi_icons[i].title;
			var i_class =zmi_icons[i].class;
			if ( $('i[title*="'+i_name+'"]').hasClass('zmi_icon-broken') ) {
			 	i_class += ' zmi_icon-broken'
			};
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
		if ( $('main').length==0 ) {
			$('body>form,body>table,body>h2,body>p').wrapAll('<main class="container-fluid zmi-patch"></main>');
		// ADD BOOTSTRAP CLASSES
			$('input[type="text"], input[type="file"], textarea, select').addClass('form-control zmi-patch');
			$('input[type="submit"]').addClass('btn btn-primary zmi-patch');
			$('textarea[name*=":text"]').addClass('zmi-code');
			$('table').addClass('table zmi-patch');
		}
	}
// [3] GUI FIX FOR MODAL DIALOG: Add Minimal Style Patches to Ancient Zope Forms
	function fix_ancient_modal_gui() {
		if ( $('.modal-body main').length==0 ) {
			$('.modal-body>form,.modal-body>table,.modal-body>h2,.modal-body>p,.modal-body>i.zmi-help-icon').wrapAll('<main class="container-fluid zmi-patch"></main>');
		// ADD BOOTSTRAP CLASSES
			$('.modal-body input[type="text"],.modal-body input[type="file"],.modal-body textarea,.modal-body select').addClass('form-control zmi-patch');
			$('.modal-body input[type="submit"]').addClass('btn btn-primary zmi-patch');
			$('.modal-body textarea[name*=":text"]').addClass('zmi-code');
			$('.modal-body table').addClass('table zmi-patch');
		}
	}


// ++++++++++++++++++++++++++
// EXECUTE ON DOCUMENT READY
// ++++++++++++++++++++++++++
$(function() {

// EXECUTE DESIGN WORKAROUNDS
// Needed until ALL GUI Forms are Bootstrap Conformant 
	fix_zmi_icons() 
	fix_ancient_gui();

// EXECUTE FUNCTIONAL WORKAROUNDS 
// [1] Showing some Menu Elements only on List Page as Active
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
	
	if (!window.matchMedia || (window.matchMedia("(max-width: 767px)").matches)) {
		$('.zmi header.navbar li.zmi-authenticated_user').tooltip({'placement':'bottom'});
	}

});


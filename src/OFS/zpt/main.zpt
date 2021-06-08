<tal:header replace="structure here/manage_page_header" />

<tal:tabs replace="structure here/manage_tabs" />

<main class="container-fluid">
  <form id="objectItems" name="objectItems" method="post"
        tal:define="has_order_support python:getattr(here.aq_explicit, 'has_order_support', 0);
                    sm modules/AccessControl/getSecurityManager;
                    default_sort python: 'position' if has_order_support else 'id';
                    skey python:request.get('skey',default_sort);
                    rkey python:request.get('rkey','asc');
                    rkey_alt python:'desc' if rkey=='asc' else 'asc';
                    rkey_alt_up rkey_alt/upper;
                    obs python: here.manage_get_sortedObjects(sortkey = skey, revkey = rkey);
                    my_url string:${context/absolute_url}/manage_main;
                   "
        tal:attributes="action string:${request/URL1}/">

    <tal:not-empty condition="obs">
      <table class="table table-striped table-hover table-sm objectItems" tal:condition="obs">
        <thead class="thead-light" tal:attributes="class python:'thead-light sorted_%s'%(request.get('rkey',''))">
          <tr>
            <th scope="col" class="zmi-object-check text-right">
              <input type="checkbox" id="checkAll" onclick="checkbox_all();" />
            </th>
            <th scope="col" class="zmi-object-type">
              <a title="Sort Ascending by Meta-Type"
                 href="?skey=meta_type&rkey=asc"
                 tal:attributes="title string:Sort ${rkey_alt_up} by meta-type;
                                 href string:${my_url}?skey=meta_type&rkey=${rkey_alt};
                                 class python:skey=='meta_type' and 'zmi-sort_key' or None;
                                ">
                <i class="fa fa-sort"></i>
              </a>
            </th>
            <th scope="col" class="zmi-object-id">
              <a title="Sort Ascending by Name"
                 href="?skey=id&rkey=asc"
                 tal:attributes="title string:Sort ${rkey_alt_up} by name;
                                 href string:${my_url}?skey=id&rkey=${rkey_alt};
                                 class python:skey=='id' and 'zmi-sort_key' or None;
                                ">
                Name
                <i class="fa fa-sort"></i>
              </a>
              <i class="fa fa-search tablefilter" onclick="$('#tablefilter').focus()"></i>
              <input id="tablefilter" name="obj_ids:tokens" type="text" title="Filter object list by entering a name. Pressing the Enter key starts recursive search." />
            </th>
            <th scope="col" class="zmi-object-size text-right hidden-xs">
              <a title="Sort Ascending by File-Size"
                 href="?skey=get_size&rkey=asc"
                 tal:attributes="title string:Sort ${rkey_alt_up} by size;
                                 href string:${my_url}?skey=get_size&rkey=${rkey_alt};
                                 class python:skey=='get_size' and 'zmi-sort_key' or None;
                                ">
                Size
                <i class="fa fa-sort"></i>
              </a>
            </th>
            <th scope="col" class="zmi-object-date text-right hidden-xs">
              <a title="Sort Ascending by Modification Date"
                 href="?skey=_p_mtime&rkey=asc"
                 tal:attributes="title string:Sort ${rkey_alt_up} by modification date;
                                 href string:${my_url}?skey=_p_mtime&rkey=${rkey_alt};
                                 class python:skey=='_p_mtime' and 'zmi-sort_key' or None;
                                ">
                Last Modified
                <i class="fa fa-sort"></i>
              </a>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr tal:repeat="ob_dict obs">
            <tal:obj define="ob nocall:ob_dict/obj">
              <td class="zmi-object-check text-right" onclick="$(this).children('input').trigger('click');">
                <input type="checkbox" class="checkbox-list-item" name="ids:list" tal:attributes="value ob_dict/id" 
                  onclick="event.stopPropagation();select_objectitem($(this));" />
              </td>
              <td class="zmi-object-type" onclick="$(this).prev().children('input').trigger('click')">
                <i title="Broken object" class="fas fa-ban text-danger" tal:attributes="class ob/zmi_icon | default; title ob/meta_type | default">
                  <span class="sr-only" tal:content="ob/meta_type | default">Broken object</span>
                </i>
              </td>
              <td class="zmi-object-id">
                <a tal:attributes="href python:'%s/manage_workspace'%(ob_dict['quoted_id'])">
                  <span tal:replace="ob_dict/id">Id</span>
                  <span class="badge badge-warning" title="This item has been locked by WebDAV" tal:condition="ob/wl_isLocked | nothing">
                    <i class="fa fa-lock"></i>
                  </span>
                  <span class="zmi-object-title hidden-xs" tal:condition="ob/title|nothing">
                    &nbsp;(<span tal:replace="ob/title"></span>)
                  </span>
                </a>
              </td>
              <td class="text-right zmi-object-size hidden-xs" tal:content="python:here.compute_size(ob)">
              </td>
              <td class="text-right zmi-object-date hidden-xs pl-3" tal:content="python:here.last_modified(ob)">
              </td>
            </tal:obj>
          </tr>
        </tbody>
      </table>

      <div class="form-group form-inline zmi-controls" tal:define="
        delete_allowed python:sm.checkPermission('Delete objects', context)" tal:condition="obs">
        <div class="input-group">
          <tal:copy-paste condition="not:context/dontAllowCopyAndPaste|nothing">
            <input class="btn btn-primary mr-2" type="submit" name="manage_renameForm:method" value="Rename" />
            <input class="btn btn-primary mr-2" type="submit" name="manage_cutObjects:method" value="Cut" tal:condition="delete_allowed" />
            <input class="btn btn-primary mr-2" type="submit" name="manage_copyObjects:method" value="Copy" />
            <input class="btn btn-primary mr-2" type="submit" name="manage_pasteObjects:method" value="Paste" tal:condition="here/cb_dataValid" />
          </tal:copy-paste>
          <input class="btn btn-primary mr-2" type="submit" name="manage_delObjects:method" value="Delete" tal:condition="delete_allowed" />
          <input class="btn btn-primary mr-2" type="submit" name="manage_importExportForm:method" value="Import/Export" tal:condition="python:sm.checkPermission('Import/Export objects', context)" />

          <div class="input-group" tal:condition="python: has_order_support and sm.checkPermission('Manage properties', context)">
            <select class="form-control btn btn-primary" name="delta:int">
              <option tal:repeat="val python:range(1,min(5,len(obs)))" tal:content="val" />
              <option tal:repeat="val python:range(5,len(obs),5)" tal:content="val" />
            </select>
            <div class="input-group-append">
              <button type="submit" name="manage_move_objects_up:method" value="Move up" 
                title="Move selected items up" class="btn btn-primary">
                <i class="fas fa-arrow-up"></i>
              </button>
              <button type="submit" name="manage_move_objects_down:method" value="Move down" 
                title="Move selected items down" class="btn btn-primary rounded-right">
                <i class="fas fa-arrow-down"></i>
              </button>
            </div>
            <button type="submit" name="manage_move_objects_to_top:method" value="Move to top" 
              title="Move selected items to top" class="btn btn-primary ml-2 mr-2">
              <i class="fas fa-arrow-up" style="border-top: 0.2rem solid silver;"></i>
            </button>
            <button type="submit" name="manage_move_objects_to_bottom:method" value="Move to bottom" 
               title="Move selected items to bottom" class="btn btn-primary">
              <i class="fas fa-arrow-down" style="border-bottom: 0.2rem solid silver;"></i>
            </button>
          </div>
        </div>

      </div>
    </tal:not-empty>

    <tal:empty condition="not:obs">
      <div class="alert alert-info mt-4 mb-4">
        There are currently no items in <em tal:content="here/title_or_id"></em>.
      </div>
      <div class="form-group">
        <tal:copy-paste condition="not:context/dontAllowCopyAndPaste|nothing">
          <input class="btn btn-primary" type="submit" name="manage_pasteObjects:method" value="Paste" tal:condition="here/cb_dataValid" />
        </tal:copy-paste>
        <input class="btn btn-primary" type="submit" name="manage_importExportForm:method" value="Import/Export" tal:condition="python:sm.checkPermission('Import/Export objects', context)" />
      </div>
    </tal:empty>
  </form>

</main>


<script>
  // +++++++++++++++++++++++++++
  // Item  Selection
  // +++++++++++++++++++++++++++
  function checkbox_all() {
    var checkboxes = document.getElementsByClassName('checkbox-list-item');
    // Toggle Highlighting CSS-Class
    if (document.getElementById('checkAll').checked) {
      $('table.objectItems tbody tr').addClass('checked');
    } else {
      $('table.objectItems tbody tr').removeClass('checked');
    };
    // Set Checkbox like checkAll-Box
    for (i = 0; i < checkboxes.length; i++) {
      checkboxes[i].checked = document.getElementById('checkAll').checked;
    }
  };

  function zmicontrols_visible() {
    var zmicontrols = $('form#objectItems .zmi-controls');
    var zmicontrols_top = zmicontrols.offset().top;
    var zmicontrols_bottom = zmicontrols_top + zmicontrols.outerHeight();
    var viewport_top = $(window).scrollTop();
    var viewport_bottom = viewport_top + $(window).height();
    return zmicontrols_bottom > viewport_top && zmicontrols_top < viewport_bottom;
  };

  function select_objectitem(ob) {
    ob.parent().parent().toggleClass('checked');
    if ( !zmicontrols_visible() ) {
      $('form#objectItems').addClass('selected');
    }
    // Anything selected?
    var checkboxes = document.getElementsByClassName('checkbox-list-item');
    var selected = false;
    for (i = 0; i < checkboxes.length; i++) {
      if ( checkboxes[i].checked ) {
        selected = true;
        break;
      }
    }
    if ( !selected ) {
      $('form#objectItems').removeClass('selected');
      console.log('form#objectItems removed .selected');
    }
  };


  $(function () {

    // +++++++++++++++++++++++++++
    // Icon Tooltips
    // +++++++++++++++++++++++++++
    $('td.zmi-object-type i').tooltip({
      'placement': 'top'
    });

    // +++++++++++++++++++++++++++
    // Tablefilter/Search Element
    // +++++++++++++++++++++++++++

    function isModifierKeyPressed(event) {
      return event.altKey ||
        event.ctrlKey ||
        event.metaKey;
    }

    $(document).keypress(function (event) {

      if (isModifierKeyPressed(event)) {
        return; // ignore
      }

      // Set Focus to Tablefilter only when Modal Dialog is not Shown
      if (!$('#zmi-modal').hasClass('show')) {
        $('#tablefilter').focus();
        // Prevent Submitting a form by hitting Enter
        // https://stackoverflow.com/questions/895171/prevent-users-from-submitting-a-form-by-hitting-enter
        if (event.which == 13) {
          event.preventDefault();
          return false;
        };
      };
    })

    $('#tablefilter').keyup(function (event) {

      if (isModifierKeyPressed(event)) {
        return; // ignore
      }

      var tablefilter = $(this).val();
      if (event.which == 13) {
        if (1 === $('tbody tr:visible').length) {
          window.location.href = $('tbody tr:visible a').attr('href');
        } else {
          window.location.href = 'manage_findForm?btn_submit=Find&search_sub:int=1&obj_ids%3Atokens=' + tablefilter;
        }
        event.preventDefault();
      };
      $('table.objectItems').find("tbody tr").hide();
      $('table.objectItems').find("tbody tr td.zmi-object-id a:contains(" + tablefilter + ")").closest('tbody tr').show();
    });

    // +++++++++++++++++++++++++++
    // OBJECTIST SORTING: Show skey=meta_type
    // +++++++++++++++++++++++++++
    let searchParams = new URLSearchParams(window.location.search);
    if (searchParams.get('skey') == 'meta_type') {
      $('td.zmi-object-type i').each(function () {
        $(this).parent().parent().find('td.zmi-object-id').prepend('<span class="zmi-typename_show">' + $(this).text() + '</span>')
      });
      $('th.zmi-object-id').addClass('zmi-typename_show');
    }

  });

</script>

<tal:footer replace="structure here/manage_page_footer" />

package de.tosox.appear_offline
{
   // Injects the Appear Offline options into the native Contacts > Settings view
   // (alias "ContactsSettingsView"). Compiled with mxmlc against minimal stubs
   // (see as3/stubs); net.wg.* classes are provided by the game at runtime.
   import flash.display.MovieClip;
   import flash.display.DisplayObjectContainer;

   import net.wg.data.constants.generated.LAYER_NAMES;
   import net.wg.infrastructure.base.AbstractView;
   import net.wg.infrastructure.events.LoaderEvent;

   import de.tosox.appear_offline.SettingsUI;

   public class LobbyHook extends AbstractView
   {
      public static const CONTACTS_SETTINGS_ALIAS:String = "ContactsSettingsView";

      // Bound by the DAAPI bridge to the same-named methods on the Python view.
      public var getAppearOfflineSettings:Function;
      public var setAppearOfflineSettings:Function;

      private var _searchTries:int = 0;

      private function _getContainer(containerName:String) : *
      {
         return App.containerMgr.getContainer(LAYER_NAMES.LAYER_ORDER.indexOf(containerName));
      }

      override protected function onPopulate() : void
      {
         super.onPopulate();
         var viewContainer:* = _getContainer(LAYER_NAMES.VIEWS);
         if(viewContainer != null)
         {
            var num:int = viewContainer.numChildren;
            for(var idx:int = 0; idx < num; ++idx)
            {
               processView(viewContainer.getChildAt(idx));
            }
            var topmostView:* = viewContainer.getTopmostView();
            if(topmostView != null)
            {
               viewContainer.setFocusedView(topmostView);
            }
         }
         App.containerMgr.loader.addEventListener(LoaderEvent.VIEW_LOADED, onViewLoaded, false, 0, true);
      }

      // Re-parent to App root so focus/position stay valid (esp. login window).
      override protected function nextFrameAfterPopulateHandler() : void
      {
         super.nextFrameAfterPopulateHandler();
         if(parent != App.instance)
         {
            (App.instance as MovieClip).addChild(this);
         }
      }

      // Called from Python when the Contacts settings view opens. That view is a
      // sub-view that doesn't fire VIEW_LOADED on the main loader, so we locate
      // it in the display tree by its native 'cbIsShowOthers' checkbox.
      public function injectContacts() : void
      {
         _searchTries = 0;
         App.utils.scheduler.scheduleOnNextFrame(this.doSearchInject);
      }

      private function doSearchInject() : void
      {
         var root:DisplayObjectContainer = (this.stage != null ? this.stage : (App.instance as DisplayObjectContainer));
         var found:DisplayObjectContainer = findByChildName(root, "cbIsShowOthers");
         if(found == null)
         {
            _searchTries++;
            if(_searchTries < 12)
            {
               App.utils.scheduler.scheduleOnNextFrame(this.doSearchInject);
            }
            return;
         }
         new SettingsUI(found, getAppearOfflineSettings(), setAppearOfflineSettings);
      }

      private function findByChildName(node:DisplayObjectContainer, childName:String) : DisplayObjectContainer
      {
         if(node == null)
         {
            return null;
         }
         if(node.getChildByName(childName) != null)
         {
            return node;
         }
         var n:int = node.numChildren;
         for(var i:int = 0; i < n; ++i)
         {
            var child:DisplayObjectContainer = node.getChildAt(i) as DisplayObjectContainer;
            if(child != null)
            {
               var r:DisplayObjectContainer = findByChildName(child, childName);
               if(r != null)
               {
                  return r;
               }
            }
         }
         return null;
      }

      private function onViewLoaded(_event:LoaderEvent) : void
      {
         processView(_event.view);
      }

      private function processView(view:*) : void
      {
         if(view == null)
         {
            return;
         }
         var alias:String = null;
         try
         {
            alias = view.as_config.alias;
         }
         catch(e:*)
         {
            return;
         }
         if(alias == CONTACTS_SETTINGS_ALIAS)
         {
            new SettingsUI(view, getAppearOfflineSettings(), setAppearOfflineSettings);
         }
      }
   }
}

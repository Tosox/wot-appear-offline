package de.tosox.appear_offline
{
   import flash.display.MovieClip;
   import flash.display.DisplayObjectContainer;

   import net.wg.infrastructure.base.AbstractView;

   import de.tosox.appear_offline.SettingsUI;

   public class LobbyHook extends AbstractView
   {
      // Bound by the DAAPI bridge to the Python view methods of the same name
      public var getAppearOfflineSettings:Function;
      public var setAppearOfflineSettings:Function;

      // Remaining frames we are willing to wait for the target panel to build itself
      private var _searchTries:int = 0;

      override protected function nextFrameAfterPopulateHandler() : void
      {
         super.nextFrameAfterPopulateHandler();
         // Reparent under the app root so we sit on the stage and can reach every view
         if(parent != App.instance)
         {
            (App.instance as MovieClip).addChild(this);
         }
      }

      // Called from Python the moment ContactsSettingsView populates
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
            // The panel's children are built over several frames, so the anchor may not exist yet
            _searchTries++;
            if(_searchTries < 12)
            {
               App.utils.scheduler.scheduleOnNextFrame(this.doSearchInject);
            }
            return;
         }
         // Anchor found, its parent is the real settings panel; hand it to SettingsUI
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
   }
}

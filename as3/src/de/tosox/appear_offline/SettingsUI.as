package de.tosox.appear_offline
{
   // Injects the two Appear Offline checkboxes into the native Contacts >
   // Settings view, using the game's own CLIK CheckBox (no custom artwork).
   // They sit in their own section below the native Apply/Cancel bar, separated
   // by a divider line. Toggling calls back to Python (which saves + notifies;
   // the change takes effect on next login).
   import flash.display.DisplayObject;
   import flash.display.DisplayObjectContainer;
   import flash.display.Sprite;
   import flash.events.Event;

   import net.wg.gui.components.controls.CheckBox;

   public class SettingsUI
   {
      private static const ENABLED_CB_NAME:String = "appearOfflineEnabledCb";
      private static const SEE_OTHERS_CB_NAME:String = "appearOfflineSeeOthersCb";
      private static const SEP_NAME:String = "appearOfflineSeparator";

      private var _callback:Function = null;
      private var _settings:Object = null;
      private var _view:DisplayObjectContainer = null;
      private var _cbEnabled:CheckBox = null;
      private var _cbSeeOthers:CheckBox = null;

      public function SettingsUI(view:*, settings:Object, callback:Function)
      {
         this._callback = callback;
         this._settings = settings;
         this._view = view as DisplayObjectContainer;
         if(this._view == null)
         {
            return;
         }
         App.utils.scheduler.scheduleOnNextFrame(this.inject);
      }

      private function inject() : void
      {
         if(this._view == null)
         {
            return;
         }
         // Guard against double injection (view stays alive across tab switches).
         if(this._view.getChildByName(ENABLED_CB_NAME) != null)
         {
            return;
         }

         var anchor:DisplayObject = this._view.getChildByName("cbIsShowOthers");
         var baseX:Number = anchor != null ? anchor.x : 20;

         // Match the native row spacing (distance between the two native rows).
         var cbOffline:DisplayObject = this._view.getChildByName("cbIsShowOfflineUsers");
         var rowGap:Number = (anchor != null && cbOffline != null) ? (anchor.y - cbOffline.y) : 30;
         if(rowGap < 20)
         {
            rowGap = 30;
         }

         // Our section goes below the native Apply/Cancel bar, anchored to the OK
         // button's bottom (btns.height reports a large padded box).
         var sectionTop:Number = (anchor != null ? anchor.y + rowGap * 2 : 120);
         var panelW:Number = this._view.width;
         try
         {
            var btns:* = this._view["btns"];
            if(btns != null && btns.btnOk != null)
            {
               sectionTop = btns.y + btns.btnOk.y + btns.btnOk.height;
            }
         }
         catch(eb:*)
         {
         }

         var sepY:Number = sectionTop + 10;
         var firstY:Number = sepY + 14;

         // Divider line above our section.
         var sep:Sprite = new Sprite();
         sep.name = SEP_NAME;
         var sepW:Number = (panelW > baseX * 2 + 40) ? (panelW - baseX * 2) : 250;
         sep.graphics.lineStyle(1, 0xFFFFFF, 0.2);
         sep.graphics.moveTo(0, 0);
         sep.graphics.lineTo(sepW, 0);
         sep.x = baseX;
         sep.y = sepY;
         this._view.addChild(sep);

         this._cbEnabled = App.utils.classFactory.getComponent("CheckBox", CheckBox);
         this._cbEnabled.name = ENABLED_CB_NAME;
         this._cbEnabled.label = this._settings.labelEnabled;
         this._cbEnabled.selected = this._settings.enabled;
         this._cbEnabled.width = 260;
         this._cbEnabled.x = baseX;
         this._cbEnabled.y = firstY;

         this._cbSeeOthers = App.utils.classFactory.getComponent("CheckBox", CheckBox);
         this._cbSeeOthers.name = SEE_OTHERS_CB_NAME;
         this._cbSeeOthers.label = this._settings.labelSeeOthers;
         this._cbSeeOthers.selected = this._settings.seeOthers;
         this._cbSeeOthers.enabled = this._settings.enabled;
         this._cbSeeOthers.width = 260;
         this._cbSeeOthers.x = baseX;
         this._cbSeeOthers.y = firstY + rowGap;

         this._cbEnabled.addEventListener(Event.SELECT, this.onChanged);
         this._cbSeeOthers.addEventListener(Event.SELECT, this.onChanged);

         // Add to the view BEFORE the info icon: CheckBox.createInfoIco() derives
         // its 'owner' from parent, so it NPEs if validated without a parent.
         this._view.addChild(this._cbEnabled);
         this._view.addChild(this._cbSeeOthers);

         // Warning icon + tooltip next to the "see others" label (like the native
         // Reticle > Armor Flashlight "Performance Warning"). "warning" is
         // InfoIcon.TYPE_WARNING; the literal avoids a class reference.
         try
         {
            if(this._settings.seeOthersTooltip != null && String(this._settings.seeOthersTooltip).length > 0)
            {
               this._cbSeeOthers.toolTip = this._settings.seeOthersTooltip;
               this._cbSeeOthers.infoIcoType = "warning";
            }
         }
         catch(eIco:*)
         {
         }

         this._cbEnabled.validateNow();
         this._cbSeeOthers.validateNow();

         // Grow the panel so our section fits under the button bar.
         try
         {
            var contentBottom:Number = firstY + rowGap + 18;
            var grow:Number = contentBottom - this._view.height;
            if(grow > 0)
            {
               this._view["setViewSize"](this._view.width, this._view.height + grow);
            }
         }
         catch(eg:*)
         {
         }
      }

      private function onChanged(_event:Event) : void
      {
         this._cbSeeOthers.enabled = this._cbEnabled.selected;
         if(this._callback != null)
         {
            this._callback(this._cbEnabled.selected, this._cbSeeOthers.selected);
         }
      }
   }
}

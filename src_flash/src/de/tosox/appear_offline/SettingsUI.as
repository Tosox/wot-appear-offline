package de.tosox.appear_offline
{
   import flash.display.DisplayObject;
   import flash.display.DisplayObjectContainer;
   import flash.display.Sprite;
   import flash.events.Event;

   import net.wg.gui.components.controls.CheckBox;

   public class SettingsUI
   {
      private static const ENABLED_CB_NAME:String = "appearOfflineEnabledCb";
      private static const SEE_OTHERS_CB_NAME:String = "appearOfflineSeeOthersCb";
      private static const CLAN_CB_NAME:String = "appearOfflineClanCb";
      private static const SEP_NAME:String = "appearOfflineSeparator";

      private static const MIN_CB_WIDTH:Number = 260;

      private var _callback:Function = null;
      private var _settings:Object = null;
      private var _view:DisplayObjectContainer = null;
      private var _cbEnabled:CheckBox = null;
      private var _cbSeeOthers:CheckBox = null;
      private var _cbClan:CheckBox = null;

      public function SettingsUI(view:*, settings:Object, callback:Function)
      {
         this._callback = callback;
         this._settings = settings;
         this._view = view as DisplayObjectContainer;
         if(this._view == null || this._settings == null)
         {
            return;
         }

         // Wait one frame so the panel has finished laying out before we measure it
         App.utils.scheduler.scheduleOnNextFrame(this.inject);
      }

      private function inject() : void
      {
         if(this._view == null)
         {
            return;
         }

         // Check if already injected
         if(this._view.getChildByName(ENABLED_CB_NAME) != null)
         {
            return;
         }

         // Line our column up with the panel's existing "Show Others" checkbox
         var anchor:DisplayObject = this._view.getChildByName("cbIsShowOthers");
         var baseX:Number = anchor != null ? anchor.x : 20;

         // Reuse the vertical gap between the panel's own two checkboxes as our row height
         var cbOffline:DisplayObject = this._view.getChildByName("cbIsShowOfflineUsers");
         var rowGap:Number = (anchor != null && cbOffline != null) ? (anchor.y - cbOffline.y) : 30;
         if(rowGap < 20)
         {
            rowGap = 30;
         }

         // Place our section below the panel's controls, or below the OK button if there is one
         var sectionTop:Number = (anchor != null ? anchor.y + rowGap * 2 : 120);
         var panelW:Number = this._view.width;
         var btns:* = this._view["btns"];
         if(btns != null && btns.btnOk != null)
         {
            sectionTop = btns.y + btns.btnOk.y + btns.btnOk.height;
         }

         var sepY:Number = sectionTop + 10;
         var firstY:Number = sepY + 14;

         // Divider between the game's options and ours
         var sep:Sprite = new Sprite();
         sep.name = SEP_NAME;
         var sepW:Number = (panelW > baseX * 2 + 40) ? (panelW - baseX * 2) : MIN_CB_WIDTH;
         sep.graphics.lineStyle(1, 0xFFFFFF, 0.2);
         sep.graphics.moveTo(0, 0);
         sep.graphics.lineTo(sepW, 0);
         sep.x = baseX;
         sep.y = sepY;
         this._view.addChild(sep);

         // Give the labels the panel's full usable width; some translations are long
         var cbW:Number = sepW > MIN_CB_WIDTH ? sepW : MIN_CB_WIDTH;

         // Build all three rows with the game's own CLIK CheckBox so they match the UI
         this._cbEnabled = this.makeCheckBox(ENABLED_CB_NAME, this._settings.labelEnabled, this._settings.enabled, baseX, firstY, cbW);
         this._cbSeeOthers = this.makeCheckBox(SEE_OTHERS_CB_NAME, this._settings.labelSeeOthers, this._settings.seeOthers, baseX, firstY + rowGap, cbW);
         this._cbClan = this.makeCheckBox(CLAN_CB_NAME, this._settings.labelVisibleToClan, this._settings.visibleToClan, baseX, firstY + rowGap * 2, cbW);

         // Both sub-options only apply while appear-offline is on
         this._cbSeeOthers.enabled = this._settings.enabled;
         this._cbClan.enabled = this._settings.enabled;

         // Warning icons flagging what each sub-option costs
         this.applyTooltip(this._cbSeeOthers, this._settings.seeOthersTooltip);
         this.applyTooltip(this._cbClan, this._settings.visibleToClanTooltip);

         this._cbEnabled.validateNow();
         this._cbSeeOthers.validateNow();
         this._cbClan.validateNow();

         // Grow the panel if our rows would spill past its current bottom edge
         var contentBottom:Number = firstY + rowGap * 2 + 18;
         var grow:Number = contentBottom - this._view.height;
         if(grow > 0)
         {
            this._view["setViewSize"](this._view.width, this._view.height + grow);
         }
      }

      private function makeCheckBox(name:String, label:String, selected:Boolean, x:Number, y:Number, width:Number) : CheckBox
      {
         var cb:CheckBox = App.utils.classFactory.getComponent("CheckBox", CheckBox);
         cb.name = name;
         cb.label = label;
         cb.selected = selected;
         cb.width = width;
         cb.x = x;
         cb.y = y;
         cb.addEventListener(Event.SELECT, this.onChanged);
         this._view.addChild(cb);
         return cb;
      }

      private function applyTooltip(cb:CheckBox, tooltip:*) : void
      {
         if(tooltip != null && String(tooltip).length > 0)
         {
            cb.toolTip = String(tooltip);
            cb.infoIcoType = "warning";
         }
      }

      private function onChanged(_event:Event) : void
      {
         // Keep the sub-options greyed out unless appear-offline is ticked, then notify Python
         this._cbSeeOthers.enabled = this._cbEnabled.selected;
         this._cbClan.enabled = this._cbEnabled.selected;
         if(this._callback != null)
         {
            this._callback(this._cbEnabled.selected, this._cbSeeOthers.selected, this._cbClan.selected);
         }
      }
   }
}

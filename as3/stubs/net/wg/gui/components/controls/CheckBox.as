package net.wg.gui.components.controls
{
   import flash.display.Sprite;

   // Stub for the game's CLIK CheckBox. Only the members we touch are declared;
   // x/y/width/name/addEventListener come from the DisplayObject/Sprite base.
   public class CheckBox extends Sprite
   {
      public var label:String;

      public var selected:Boolean;

      public var enabled:Boolean;

      // Optional info/warning icon shown next to the label, with a tooltip.
      public var infoIcoType:String;

      public var toolTip:String;

      public function CheckBox()
      {
         super();
      }

      public function validateNow() : void
      {
      }
   }
}

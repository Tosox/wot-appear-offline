package net.wg.infrastructure.events
{
   import flash.events.Event;

   public class LoaderEvent extends Event
   {
      public static var VIEW_LOADED:String;

      public var view:*;

      public function LoaderEvent(type:String = "")
      {
         super(type);
      }
   }
}

package net.wg.infrastructure.events
{
   import flash.events.Event;

   // Stub. VIEW_LOADED is a 'var' (not const) so the compiler emits a runtime
   // property read instead of inlining a wrong value; the real value comes
   // from the game's LoaderEvent at runtime.
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

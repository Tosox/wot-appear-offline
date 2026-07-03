package net.wg.infrastructure.base
{
   import flash.display.MovieClip;

   // Stub. onPopulate() is FIRST declared here in the real hierarchy, so
   // declaring it here gives our override the correct protected-namespace URI
   // (derived from this class's fully-qualified name) to bind at runtime.
   public class BaseDAAPIComponent extends MovieClip
   {
      public function BaseDAAPIComponent()
      {
         super();
      }

      protected function onPopulate() : void
      {
      }
   }
}

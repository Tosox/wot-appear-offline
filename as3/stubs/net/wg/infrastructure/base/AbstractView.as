package net.wg.infrastructure.base
{
   import net.wg.infrastructure.base.meta.impl.AbstractViewMeta;

   // Stub. nextFrameAfterPopulateHandler() is first declared in the real
   // AbstractView, so declaring it here binds our override at runtime.
   public class AbstractView extends AbstractViewMeta
   {
      public function AbstractView()
      {
         super();
      }

      protected function nextFrameAfterPopulateHandler() : void
      {
      }
   }
}

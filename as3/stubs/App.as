package
{
   // Minimal external stub for the game's global App. Untyped members so we
   // don't have to stub App.utils / containerMgr subtypes. Real class provided
   // by the game at runtime (this stub is compiled external, not embedded).
   public class App
   {
      public static var utils:*;
      public static var instance:*;
      public static var containerMgr:*;
   }
}

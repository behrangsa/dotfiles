#!/usr/bin/env bash
gdbus call \
  --session \
  --dest org.gnome.Shell \
  --object-path /org/gnome/Shell \
  --method org.gnome.Shell.Eval \
  "try {
     const { Meta } = imports.gi;
     // all window actors
     let actors = global.get_window_actors();
     // find focused
     let focusedActor = actors.find(a => a.meta_window.has_focus());
     if (!focusedActor) throw 'No focused window!';
     let focusWin = focusedActor.meta_window;
     // minimize all other NORMAL, mapped, non-minimized windows
     actors
       .map(a => a.meta_window)
       .filter(w =>
         w &&
         w !== focusWin &&
         w.get_window_type() === Meta.WindowType.NORMAL &&
         !w.minimized &&
         w.showing_on_its_workspace()
       )
       .forEach(w => w.minimize());
     true;
   } catch (e) {
     log('Minimize-other-windows error: ' + e);
     '' + e;
   }"



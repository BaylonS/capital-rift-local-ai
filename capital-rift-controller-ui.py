#!/usr/bin/env python3
"""Task window for the reviewed local Capital Rift controller (system Python/Tk)."""
import json
import os
from pathlib import Path
import subprocess
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

HOME = Path.home()
ROOT = HOME / 'capital-rift-controller'
BACKEND = HOME / 'capital-rift-controller.py'
PYTHON = HOME / 'capital-rift-env/bin/python'
ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
ENV = dict(os.environ, DISPLAY=':0', XAUTHORITY=str(HOME / '.Xauthority'))

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('Capital Rift — Local Llama Controller')
        self.root.geometry('860x650')
        self.plan = None
        self.busy = False
        self.cancelled = False
        ttk.Label(self.root, text='Tell your local Llama what to do', font=('Sans', 16, 'bold')).pack(anchor='w', padx=18, pady=(16, 5))
        ttk.Label(self.root, text='Explore the map and inspect items • Review edits separately • runs locally').pack(anchor='w', padx=18)
        self.goal = tk.Text(self.root, height=4, wrap='word', font=('Sans', 12))
        self.goal.pack(fill='x', padx=18, pady=10)
        saved_goal = ROOT / 'goal.txt'
        self.goal.insert('1.0', saved_goal.read_text() if saved_goal.exists() else 'Inspect the selected company’s logistics. Find why production stops. Verify the company and read the current wiki before changing anything.')
        bar = ttk.Frame(self.root); bar.pack(fill='x', padx=18)
        self.observe_button = ttk.Button(bar, text='Observe & propose next action', command=self.observe)
        self.observe_button.pack(side='left')
        self.apply_button = ttk.Button(bar, text='Apply reviewed action', command=self.apply, state='disabled')
        self.apply_button.pack(side='left', padx=8)
        self.explore_button = ttk.Button(bar, text='Explore & inspect (3 steps)', command=self.explore)
        self.explore_button.pack(side='left', padx=4)
        ttk.Button(bar, text='STOP', command=self.stop).pack(side='right')
        self.status = tk.StringVar(value='Ready. Keep Capital Rift open in Chrome. Allow 1–3 minutes per observation on this server.')
        ttk.Label(self.root, textvariable=self.status, wraplength=800).pack(anchor='w', padx=18, pady=10)
        self.output = tk.Text(self.root, wrap='word', font=('Sans', 11), state='disabled')
        self.output.pack(fill='both', expand=True, padx=18, pady=(0, 12))
        ttk.Label(self.root, text='Review the target before applying. Verify quantities and ownership directly. Move the mouse to a screen corner to abort input.', wraplength=800).pack(anchor='w', padx=18, pady=(0, 12))
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.show('Examples:\n\n• Zoom in, find a building and read its actual item information.\n• Inspect the selected company’s logistics and identify a stalled input.\n\nExplore & inspect can zoom, pan and open information for up to three steps, then reports what it found. It does not purchase, construct or change logistics.\n\nObserve proposes one reviewed action. Apply sends that action. Observe again to verify the result.\nThe local models can misread details; verify quantities and ownership before edits.')
        previous = ROOT / 'latest-exploration.txt'
        if previous.exists():
            self.show(previous.read_text())

    def show(self, text):
        self.output.configure(state='normal'); self.output.delete('1.0', 'end')
        self.output.insert('1.0', text); self.output.configure(state='disabled')

    def start_job(self, args, callback):
        if self.busy:
            return
        self.busy = True; self.cancelled = False
        (ROOT / 'STOP').unlink(missing_ok=True)
        self.observe_button.configure(state='disabled'); self.apply_button.configure(state='disabled')
        self.explore_button.configure(state='disabled')
        self.root.iconify()  # Keep the task window out of the captured game screen.
        def worker():
            try:
                result = subprocess.run([str(PYTHON), str(BACKEND), '--focus-game'] + args,
                                        env=ENV, text=True, capture_output=True, timeout=1800)
                self.root.after(0, self.finish, result, callback)
            except Exception as error:
                self.root.after(0, self.error, str(error))
        threading.Thread(target=worker, daemon=True).start()

    def finish(self, result, callback):
        self.busy = False
        self.root.deiconify(); self.root.lift()
        self.observe_button.configure(state='normal')
        self.explore_button.configure(state='normal')
        if self.cancelled:
            self.status.set('Stopped. Observe again for a fresh proposal.'); return
        if result.returncode:
            self.error(result.stdout.strip() or result.stderr[-2000:]); return
        callback(result.stdout)

    def error(self, text):
        self.busy = False; self.root.deiconify(); self.root.lift()
        self.observe_button.configure(state='normal'); self.apply_button.configure(state='disabled')
        self.explore_button.configure(state='normal')
        self.status.set('Stopped without sending further input. Fix the issue and observe again.')
        self.show(text)

    def observe(self):
        goal = self.goal.get('1.0', 'end').strip()
        if not goal:
            return
        (ROOT / 'goal.txt').write_text(goal)
        directory = ROOT / time.strftime('%Y%m%d-%H%M%S')
        self.plan = None
        self.status.set('Reading the game and asking local Llama for one action…')
        def ready(_):
            self.plan = directory / 'plan.json'
            plan = json.loads(self.plan.read_text())
            self.show((directory / 'review.txt').read_text())
            kind = plan['action']['action']
            self.apply_button.configure(state='normal' if kind not in ('ask', 'done', 'wait') else 'disabled')
            self.status.set('Proposal ready. Review it, then apply or ask for another observation.')
        self.start_job(['--goal', goal, '--directory', str(directory)], ready)

    def apply(self):
        if not self.plan:
            return
        self.status.set('Applying the reviewed action, then saving the resulting screen…')
        def applied(text):
            data = json.loads(text)
            self.show('INPUT SENT\n\n' + json.dumps(data['action'], indent=2) +
                      '\n\nExpected result to verify: ' + data.get('expected', '') +
                      '\n\nVisible text after input:\n' + '\n'.join(data['after_ocr']) +
                      '\n\nClick Observe to verify the outcome and choose the next step.')
            self.plan = None
            self.status.set('One action sent. Observe again to verify and continue.')
        self.start_job(['--apply', str(self.plan)], applied)

    def explore(self):
        goal = self.goal.get('1.0', 'end').strip()
        if not goal:
            return
        (ROOT / 'goal.txt').write_text(goal)
        directory = ROOT / ('explore-' + time.strftime('%Y%m%d-%H%M%S'))
        self.plan = None
        self.status.set('Exploring: zooming, panning and opening item details. Allow several minutes; STOP remains available.')
        def finished(_):
            self.show((directory / 'exploration.txt').read_text())
            self.status.set('Exploration finished. Review the item facts, then Observe for a proposed edit.')
        self.start_job(['--explore', '--steps', '3', '--goal', goal, '--directory', str(directory)], finished)

    def stop(self):
        (ROOT / 'STOP').touch(); self.cancelled = True; self.plan = None
        self.apply_button.configure(state='disabled')
        self.status.set('Stop requested. Pending model output will not be applied.')

    def close(self):
        (ROOT / 'goal.txt').write_text(self.goal.get('1.0', 'end').strip())
        self.stop(); self.root.destroy()

if __name__ == '__main__':
    App().root.mainloop()

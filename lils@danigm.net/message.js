/* exported Message */

const Main = imports.ui.main;
const GObject = imports.gi.GObject;
const Clutter = imports.gi.Clutter;
const Graphene = imports.gi.Graphene;
const St = imports.gi.St;
const MessageList = imports.ui.messageList;


const MARGIN = 30;
const ANIMATION_TIME = 500;


var Message = GObject.registerClass({
    Signals: {
        'next': {},
        'option-selected': { param_types: [GObject.TYPE_INT] },
    },
}, class Message extends St.BoxLayout {
    _init(message, options, hasNext) {
        super._init({
            style_class: 'message-box',
            clip_to_allocation: false,
            vertical: true,
            x_expand: true,
        });

        // TODO: Handle metadata in message as json, right now is plain text
        this._message = message;
        this._options = options;

        this._text = new MessageList.URLHighlighter(this._message, true, true);
        this._text.add_style_class_name('message-text');
        this.add_actor(this._text);

        this._nextButton = new St.Button({
            style_class: 'message-button',
            can_focus: true,
            x_align: Clutter.ActorAlign.END,
        });
        this._nextButton.set_icon_name('go-next-symbolic');
        this._nextButton.connect('clicked', () => {
            this.emit('next');
        });

        this._optionsBox = new St.BoxLayout({
            style_class: 'options-box',
            clip_to_allocation: true,
            vertical: true,
            x_expand: true,
        });

        if (this._options.length && !hasNext) {
            this._options.forEach((opt, i) => this.addOption(opt, i));
            this.add_actor(this._optionsBox);
        } else {
            this.add_actor(this._nextButton);
        }
    }

    addOption(opt, index) {
        const button = new St.Button({
            style_class: 'option-button',
            can_focus: true,
            x_align: Clutter.ActorAlign.START,
        });
        button.connect('clicked', () => {
            this.emit('option-selected', index);
        });
        button.set_label(opt);
        this._optionsBox.add_actor(button);
    }

    present() {
        Main.layoutManager.addChrome(this);

        const monitor = Main.layoutManager.primaryMonitor;
        if (!monitor)
            return;

        this.x = monitor.x + monitor.width;
        this.y = (monitor.y + monitor.height
                  - this.height - MARGIN
                  - Main.panel.get_height());
        this.width = monitor.width / 2 - MARGIN * 2;

        const endX = this.x - this.width - MARGIN;

        // clipping the actor to avoid appearing in the right monitor
        //
        const endClip = new Graphene.Rect({
            origin: new Graphene.Point({x: 0, y: 0}),
            size: new Graphene.Size({
                width: this.width + MARGIN,
                height: this.height,
            }),
        });
        this.set_clip(0, 0, 0, this.height);

        this.ease({
            x: endX,
            clip: endClip,
            duration: ANIMATION_TIME,
            mode: Clutter.AnimationMode.EASE_OUT_QUAD,
        });
        this.ease_property('clip-rect', endClip, {
            duration: ANIMATION_TIME,
            mode: Clutter.AnimationMode.EASE_OUT_QUAD,
            onComplete: () => this.remove_clip(),
        });
    }
});

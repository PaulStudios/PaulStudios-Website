Ball.Preloader = function(game) {};
Ball.Preloader.prototype = {
	preload: function() {
		this.preloadBg = this.add.sprite((Ball._WIDTH-297)*0.5, (Ball._HEIGHT-145)*0.5, 'preloaderBg');
		this.preloadBar = this.add.sprite((Ball._WIDTH-158)*0.5, (Ball._HEIGHT-50)*0.5, 'preloaderBar');
		this.load.setPreloadSprite(this.preloadBar);

		this.load.image('ball', assetsUrls.images.ball);
        this.load.image('hole', assetsUrls.images.hole);
        this.load.image('elementW', assetsUrls.images.elementW);
        this.load.image('elementH', assetsUrls.images.elementH);
        this.load.image('panel', assetsUrls.images.panel);
        this.load.image('title', assetsUrls.images.title);
        this.load.image('buttonPause', assetsUrls.images.buttonPause);
        this.load.image('screenBg', assetsUrls.images.screenBg);
        this.load.image('screenMainmenu', assetsUrls.images.screenMainmenu);
        this.load.image('screenHowtoplay', assetsUrls.images.screenHowtoplay);
        this.load.image('borderHorizontal', assetsUrls.images.borderHorizontal);
        this.load.image('borderVertical', assetsUrls.images.borderVertical);

        // Load spritesheets
        this.load.spritesheet('buttonAudio', assetsUrls.images.buttonAudio, { frameWidth: 35, frameHeight: 35 });
        this.load.spritesheet('buttonStart', assetsUrls.images.buttonStart, { frameWidth: 146, frameHeight: 51 });

        // Load audio files
        this.load.audio('audioBounce', [assetsUrls.audio.audioBounceOgg, assetsUrls.audio.audioBounceMp3, assetsUrls.audio.audioBounceM4a]);
	},
	create: function() {
		this.game.state.start('MainMenu');
	}
};
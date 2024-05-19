var Ball = {
	_WIDTH: 320,
	_HEIGHT: 480
};
Ball.Boot = function(game) {};
Ball.Boot.prototype = {
	preload: function() {
		this.load.image('preloaderBg', assetsUrls.images.load_bg);
		this.load.image('preloaderBar', assetsUrls.images.load_bar);
	},
	create: function() {
		this.game.scale.scaleMode = Phaser.ScaleManager.SHOW_ALL;
		this.game.scale.pageAlignHorizontally = true;
		this.game.scale.pageAlignVertically = true;
		this.game.state.start('Preloader');
	}
};
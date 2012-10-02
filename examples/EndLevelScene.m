//
//  EndLevelScene.m
//  igirl
//
//  Created by Andres
//  Copyright 2012 LVK. All rights reserved.
//

#import "EndLevelScene.h"
#import "GameScene.h"
#import "MenuScene.h"
#import "LvkLevel.h"
#import "LvkLevelsManager.h"
#import "LvkItem.h"
#import "LvkUserProfile.h"
#import "LvkProfilesManager.h"
#import "LvkMenuItemFont.h"
#import "LvkLabelWithShadow.h"
#import "LvkAudioManager.h"
#import "game_strings.h"
#import "config.h"
#import "LvkFontUtil.h"

//------------------------------------------------------------------------------------------
// EndLevelScene
//------------------------------------------------------------------------------------------

@implementation EndLevelScene

+ (EndLevelScene*) sceneWithStatus:(EndStatus)status levelPassed:(BOOL)passed andMark:(int)mark
{
	return [[[self alloc] initWithStatus:status levelPassed:passed andMark:mark] autorelease];
}

- (EndLevelScene*) initWithStatus:(EndStatus) status levelPassed:(BOOL)passed andMark:(int)mark;
{
    self = [super init];
    if (self != nil) {
		EndLevelLayer* layer = [EndLevelLayer layerWithStatus:status levelPassed:passed andMark:mark];
        [self addChild:layer];
    }
    return self;
}

@end

//------------------------------------------------------------------------------------------
// EndLevelLayer()
//------------------------------------------------------------------------------------------


@interface EndLevelLayer()

- (void) addBackground;
- (void) addTitleWithStatus:(EndStatus)status;
- (void) addMenuWithStatus:(EndStatus)status;

- (void) restart:(id)sender;
- (void) exit:(id)sender;
- (void) nextLevel:(id)sender;

- (void) tick:(ccTime)dt;

- (void) showUnlockedItem:(LvkItem *)item;

@end


//------------------------------------------------------------------------------------------
// EndLevelLayer
//------------------------------------------------------------------------------------------

#define END_LEVEL_TICK_INTERVAL	0.04

@implementation EndLevelLayer

+ (EndLevelLayer*) layerWithStatus:(EndStatus) status levelPassed:(BOOL)passed andMark:(int)mark
{
	return [[[self alloc] initWithStatus:status levelPassed:passed andMark:mark] autorelease];
}

- (EndLevelLayer*) initWithStatus:(EndStatus) status levelPassed:(BOOL)passed andMark:(int)mark
{
    self = [super init];
    if (self != nil) {
		_layerTime = 0;
		_layerState = 0;
		_tickCounter = 0;
		
		_mark = mark;
		_markLabelProgress = 0;
		
		_levelPassed = passed;
		
		_dimensions = CGSizeMake(SCR_W*0.9, SCR_H);

		_moneyEarnt = passed ? (20 + MAX(0, mark - 80)) : 0; 
		
		[self addBackground];
		[self addTitleWithStatus:status];
		[self addMenuWithStatus:status];
		
		if (passed == YES) {
			[[LvkAudioManager sharedAudioManager] playBackgroundMusic:THEME_END_LEVEL_PASSED loop:NO];
		} else {
			[[LvkAudioManager sharedAudioManager] playBackgroundMusic:THEME_END_LEVEL_NOT_PASSED loop:NO];
		}
		
		[self schedule:@selector(tick:) interval:END_LEVEL_TICK_INTERVAL];
    }
    return self;
}

- (void) addBackground
{
	CCSprite * bg = [CCSprite spriteWithFile:END_LEVEL_BG_FILE];
	[bg setPosition:END_LEVEL_BG_POS];
	[self addChild:bg z:0];	
}

- (void) addTitleWithStatus:(EndStatus)status
{
	int currentLevel = [LvkLevelsManager sharedManager].currentLevel;
	
	// title label

	NSString* title = @"";
	
	switch (status) {
		case endSt_DatePassed:
			title = (currentLevel == 1) ? STR_END_LEVEL_TITLE_DATE_0_PASSED : STR_END_LEVEL_TITLE_DATE_N_PASSED;
			break;
		case endSt_GreatTime:
			title = STR_END_LEVEL_TITLE_GREAT_TIME;
			break;
		case endSt_Regular:
			title = STR_END_LEVEL_TITLE_REGULAR;
			break;
		case endSt_Bored:
			title = STR_END_LEVEL_TITLE_BORED;
			break;
		case endSt_Anger:
			title = STR_END_LEVEL_TITLE_ANGER;
			break;			
		default:
			break;
	}

	_titleLabel = [LvkLabelWithShadow labelWithString:title dimensions:_dimensions alignment:UITextAlignmentCenter
										lineBreakMode:UILineBreakModeWordWrap fontName:END_LEVEL_TITLE_FONT_NAME 
											 fontSize:END_LEVEL_TITLE_FONT_SIZE];
	
	_titleLabel.anchorPoint = CGPointMake(0.5, 1);
	_titleLabel.position = END_LEVEL_TITLE_POS;
    _titleLabel.color = END_LEVEL_TITLE_COLOR;
	
	[self addChild:_titleLabel];
	
	// mark label
	
	CGSize titleSize = [LvkFontUtil getSizeForText:title inBox:_dimensions 
								   withFontName:END_LEVEL_TITLE_FONT_NAME size:END_LEVEL_TITLE_FONT_SIZE];
	
	_markLabel = [CCLabelTTF labelWithString:@"" dimensions:_dimensions alignment:UITextAlignmentCenter
							   lineBreakMode:UILineBreakModeWordWrap fontName:END_LEVEL_MARK_FONT_NAME 
									fontSize:END_LEVEL_MARK_FONT_SIZE];
	
	_markLabel.anchorPoint = CGPointMake(0.5, 1);
	_markLabel.position = CGPointMake(END_LEVEL_TITLE_POS.x, END_LEVEL_TITLE_POS.y - titleSize.height - END_LEVEL_MARK_OY);
    _markLabel.color = END_LEVEL_MARK_COLOR;
	
	[self addChild:_markLabel];	
}


- (void) addMenuWithStatus:(EndStatus)status
{
	if (_levelPassed == YES) {
		if ([LvkLevelsManager sharedManager].currentLevel == 1) {
			LvkMenuItemFont *itemFirstDate = [LvkMenuItemFont itemFromString:STR_MENU_ITEM_FIRST_DATE target:self selector:@selector(nextLevel:)];
			
			_menu = [CCMenu menuWithItems:itemFirstDate, nil];

		} else {
			LvkMenuItemFont *itemNextDate = [LvkMenuItemFont itemFromString:STR_MENU_ITEM_NEXT_DATE target:self selector:@selector(nextLevel:)];
			
			_menu = [CCMenu menuWithItems:itemNextDate, nil];			
		}
	} else {
		LvkMenuItemFont *itemMainMenu = [LvkMenuItemFont itemFromString:STR_MENU_ITEM_MAIN_MENU target:self selector:@selector(exit:)];
		LvkMenuItemFont *itemRetry = [LvkMenuItemFont itemFromString:STR_MENU_ITEM_RETRY target:self selector:@selector(restart:)];

		_menu = [CCMenu menuWithItems:itemRetry, itemMainMenu, nil];
	}

	_menu.position = _levelPassed ? END_LEVEL_PASSED_MENU_POS : END_LEVEL_MENU_POS;
	_menu.visible = NO;
	[_menu alignItemsVerticallyWithPadding:END_LEVEL_MENU_ITEMS_SEP];
	
	[self addChild:_menu];
}


- (void) restart:(id)sender 
{
    GameScene * gs = [GameScene node];
    [[CCDirector sharedDirector] replaceScene: [CCTransitionFade transitionWithDuration:SCENE_TRANSITION_FADE_DUR scene:gs]];
}

- (void) exit:(id)sender 
{
    MenuScene * ms = [MenuScene node];
    [[CCDirector sharedDirector] replaceScene: [CCTransitionFade transitionWithDuration:SCENE_TRANSITION_FADE_DUR scene:ms]];
}

- (void) nextLevel:(id)sender
{
    GameScene * gs = [GameScene node];
    [[CCDirector sharedDirector] replaceScene: [CCTransitionFade transitionWithDuration:SCENE_TRANSITION_FADE_DUR scene:gs]];
}

- (void) tick:(ccTime)dt
{
	_layerTime += dt;
	_tickCounter++;
	
	// State 0. Update money in profile and show money icon
	// State 1. Animate mark and money
	// State 2. Show unlocked item
	// State 3. Show menu
	// State 4. Idle state
	
	switch (_layerState) {
			
		case 0:
			if (_levelPassed == YES) {
				LvkItem *profileItemMoney = [[LvkProfilesManager currentProfile] getItemByName:ITEM_MONEY_NAME];
				
				_itemMoney = [LvkItem itemWithName:ITEM_MONEY_NAME amount:profileItemMoney.amount];
				_itemMoney.labelColor = END_LEVEL_TITLE_COLOR;
				_itemMoney.anchorPoint = _markLabel.anchorPoint;
				_itemMoney.position = ccp(_markLabel.position.x, _markLabel.position.y - END_LEVEL_MONEY_ITEM_OY);
				[self addChild:_itemMoney];
				
				profileItemMoney.amount = profileItemMoney.amount + _moneyEarnt;
			}
			
			_layerState++;
			break;

		case 1:
			_markLabelProgress = MIN(_mark, _layerTime/0.02);
			[_markLabel setString:[NSString stringWithFormat:@"%@: %d/100", STR_END_LEVEL_YOUR_MARK, _markLabelProgress]];
			
			if (_levelPassed == YES && _moneyEarnt > 0 && _tickCounter % 2 == 0) {
				[_itemMoney setAmountWithAnimation:(_itemMoney.amount + 1)];
				_moneyEarnt--;
			}
			
			if (_markLabelProgress == _mark && _moneyEarnt == 0) {
				_layerState++;
			}
			break;
		
			
		case 2:
			if (_levelPassed == YES) {
				LvkItem *unlockedItem = nil;
				
				if ([LvkLevelsManager sharedManager].currentLevel == 1) {
					unlockedItem = [LvkItem itemWithName:ITEM_FLOWER_NAME price:5];
				}
				
				if (unlockedItem != nil) {
					
					// If item already unlocked, do not show it.
					if ([[LvkProfilesManager currentProfile].itemsUnlocked containsObject:unlockedItem.name] == NO) {						
						[self showUnlockedItem:unlockedItem];
						
						_menu.position = END_LEVEL_MENU_UNLOCKED_ITEM_POS;
						
						[[LvkProfilesManager currentProfile].itemsUnlocked addObject:unlockedItem.name];
					}
					
					[[LvkProfilesManager currentProfile] addItem:unlockedItem];
					[[LvkProfilesManager sharedManager] save];
				}
			}

			_layerState++;
			break;
			
			
		case 3:
			_menu.visible = YES;
				
			_layerState++;				
			break;
	}
	
}

- (void) showUnlockedItem:(LvkItem *)item
{	
	if (_itemUnlockedLabel == nil) {
		_itemUnlockedLabel = [CCLabelTTF labelWithString:STR_END_LEVEL_CONGRAT_UNLOCK dimensions:_dimensions 
											   alignment:UITextAlignmentCenter lineBreakMode:UILineBreakModeWordWrap
												fontName:END_LEVEL_TITLE_FONT_NAME fontSize:22];
		_itemUnlockedLabel.color = GAME_MENU_SUBTITLE_COLOR;
		_itemUnlockedLabel.anchorPoint = CGPointMake(0.5, 1);
		_itemUnlockedLabel.position = END_LEVEL_UNLOCK_LABEL_POS;
		_itemUnlockedLabel.opacity = 0;
				
		[self addChild:_itemUnlockedLabel];
		
		item.position = END_LEVEL_UNLOCK_ITEM_POS;
		item.opacity = 0;
		[item hideAmountLabel];
				
		[self addChild:item];
		
		const int FADE_DURATION = 0.5;
		[_itemUnlockedLabel runAction:[CCFadeIn actionWithDuration:FADE_DURATION]];
		[item runAction:[CCFadeIn actionWithDuration:FADE_DURATION]];
	}
}

@end


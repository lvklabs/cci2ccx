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


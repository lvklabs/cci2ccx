//
//  CompanyLogoScene.m
//  igirl
//
//  Created by Andres
//  Copyright 2010 LavandaInk. All rights reserved.
//


#import "common.h"
#import "config.h"
#import "cocos2d.h"
#import "CompanyLogoScene.h"
#import "SplashScene.h"

@implementation CompanyLogoScene

- (id) init
{
    self = [super init];
    if (self != nil) {
        [self addChild:[CompanyLogoLayer node] z:0];
    }
    return self;
}

@end

@implementation CompanyLogoLayer

- (id) init
{
    self = [super init];
    if (self != nil) {
		self.isTouchEnabled = YES;
		
		_layerTime = 0;

        CCSprite * bg = [CCSprite spriteWithFile:COMPANY_LOGO_FILE];
        [bg setPosition:COMPANY_LOGO_POS];
        [self addChild:bg z:0];
		
		[self schedule:@selector(tick:) interval:TICK_INTERVAL];

    }
    return self;
}

- (void) dealloc
{
	[self unscheduleAllSelectors];
	[self removeAllChildrenWithCleanup:YES];
	
	[super dealloc];
}

- (void) tick:(ccTime) dt
{	
	_layerTime += dt;
	
	if (_layerTime >= COMPANY_LOGO_DUR) {
		static BOOL sceneReplaced = NO;
		
		if (sceneReplaced == NO) {
			[[CCDirector sharedDirector] replaceScene:[CCTransitionFade transitionWithDuration:SCENE_TRANSITION_FADE_DUR scene:[SplashScene node]]];
			sceneReplaced = YES;
		}
	}
}

+ (void) example1
{
}


- (int)  example2
{
}

- (int)  exampleWithInt:(int)i andInt:(int)j
{
}

@end

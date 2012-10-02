//
//  EndLevelScene.h
//  igirl
//
//  Created by Andres
//  Copyright 2012 LVK. All rights reserved.
//

#import "cocos2d.h"

/// end status
typedef enum {
	endSt_Null,
	endSt_Anger,
	endSt_Bored,
	endSt_Regular,	
	endSt_GreatTime,	
	endSt_DatePassed,	
} EndStatus;


@class LvkItem;

@interface EndLevelLayer : CCLayer 
{
	ccTime _layerTime;
	long _tickCounter;
	
	BOOL _levelPassed;
	int _mark;
	int _markLabelProgress;
	
	int _moneyEarnt;
		
	CCLabelTTF *_titleLabel;
	CCLabelTTF *_markLabel;
	CCLabelTTF *_itemUnlockedLabel;
	
	CGSize _dimensions;
	
	CCMenu *_menu;
	
	LvkItem *_itemMoney;
	
	int _layerState;
}

-(id) initWithStatus:(EndStatus)status levelPassed:(BOOL)passed andMark:(int)mark;
+(id) layerWithStatus:(EndStatus)status levelPassed:(BOOL)passed andMark:(int)mark;

@end



@interface EndLevelScene : CCScene
{
}

-(id) initWithStatus:(EndStatus)status levelPassed:(BOOL)passed andMark:(int)mark;
+(id) sceneWithStatus:(EndStatus)status levelPassed:(BOOL)passed andMark:(int)mark;

@end

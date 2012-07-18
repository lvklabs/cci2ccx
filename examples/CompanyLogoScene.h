//
//  CompanyLogoScene.h
//  igirl
//
//  Created by Andres
//  Copyright 2010 LavandaInk. All rights reserved.
//


#import "cocos2d.h"

@interface CompanyLogoLayer : CCLayer 
{ 
	ccTime _layerTime;
}

- (void) tick:(ccTime) dt;
+ (void) example1;
- (int)  example2;
- (int)  exampleWithInt:(int)i andInt:(int)j;

@end

@interface CompanyLogoScene : CCScene { }
@end

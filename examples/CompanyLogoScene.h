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

@end

@interface CompanyLogoScene : CCScene { }
@end

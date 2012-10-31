#TODO : parse methods code
# ([A-Z]\w+)\s+(\*\w+)\s*=\s*\[([A-Z]\w*)\s(\w*):(\w*)\]
# CCMenuItemImage *backArrow =
# [CCMenuItemImage itemFromNormalImage:GAME_BACK_ARROW_FILE]


"""
TODO: Transform this:

    CGSize dimensions = CGSizeMake(SCR_W*0.9, SCR_H);

    LvkLabelWithShadow *titleLabel = [LvkLabelWithShadow labelWithString:STR_LEVEL_SEL_TITLE dimensions:dimensions alignment:UITextAlignmentCenter
                                                           lineBreakMode:UILineBreakModeWordWrap fontName:LEVEL_SEL_TITLE_FONT_NAME
                                                                fontSize:LEVEL_SEL_TITLE_FONT_SIZE];

    titleLabel.anchorPoint = CGPointMake(0.5, 1);
    titleLabel.position = LEVEL_SEL_TITLE_POS;
    titleLabel.color = LEVEL_SEL_TITLE_COLOR;

    [self addChild:titleLabel];

Into


    CCSize dimensions = CCSizeMake(SCR_W*0.9, SCR_H);

    LvkLabelWithShadow *titleLabel = LvkLabelWithShadow::create(STR_LEVEL_SEL_TITLE, dimensions, kCCTextAlignmentCenter,
                                                                 kCCVerticalTextAlignmentCenterfontName, LEVEL_SEL_TITLE_FONT_NAME,
                                                                LEVEL_SEL_TITLE_FONT_SIZE);

    titleLabel->setAnchorPoint(CCPointMake(0.5, 1));
    titleLabel->setPosition(LEVEL_SEL_TITLE_POS);
    titleLabel->setColor(LEVEL_SEL_TITLE_COLOR);

    this->addChild(titleLabel)

"""
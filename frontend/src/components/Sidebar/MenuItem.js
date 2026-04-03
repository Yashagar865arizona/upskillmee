// src/components/Sidebar/MenuItem.js

import React from 'react';
import PropTypes from 'prop-types';
import './MenuItem.module.css'; // Ensure CSS Modules are used correctly

const MenuItem = ({ text, active }) => {
  return (
    <div className={`menu-item ${active ? 'active' : ''}`}>
      <div className="menu-icon">
        <div className="icon-border"></div>
      </div>
      <div className="menu-text">{text}</div>
    </div>
  );
};

MenuItem.propTypes = {
  text: PropTypes.string.isRequired,
  active: PropTypes.bool,
};

MenuItem.defaultProps = {
  active: false,
};

export default MenuItem;